"""
DistilBERT Symptom Model Fine-Tuning Pipeline.

Fine-tunes distilbert-base-uncased for multi-class symptom-to-condition classification.
Designed for execution on Google Colab GPU (T4/V100/A100) with CPU fallback.
Works seamlessly in environments with or without pandas/sklearn.

Usage:
    python train_symptom_model.py --data_dir ./processed --output_dir ./models/symptom --epochs 5 --batch_size 16
"""

import argparse
import csv
import json
import logging
import os
import random
import sys
import time
from collections import Counter
from typing import Dict, List, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoConfig,
    AutoModelForSequenceClassification,
    AutoTokenizer,
    get_linear_schedule_with_warmup,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("train")


class SymptomDataset(Dataset):
    """PyTorch Dataset for symptom text classification."""

    def __init__(self, texts: List[str], labels: List[int], tokenizer, max_length: int = 128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        text = str(self.texts[idx])
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )
        item = {key: val.squeeze(0) for key, val in encoding.items()}
        item["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item


def load_split_csv(filepath: str) -> Tuple[List[str], List[int]]:
    """Load text and label arrays from CSV."""
    texts = []
    labels = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row["symptoms"])
            labels.append(int(row["label"]))
    return texts, labels


def compute_metrics(
    labels: List[int], preds: List[int], num_classes: int
) -> Tuple[float, float, float, float]:
    """Compute accuracy, macro precision, macro recall, and macro F1."""
    try:
        from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

        acc = accuracy_score(labels, preds)
        macro_p = precision_score(labels, preds, average="macro", zero_division=0)
        macro_r = recall_score(labels, preds, average="macro", zero_division=0)
        macro_f1 = f1_score(labels, preds, average="macro", zero_division=0)
        return acc, macro_p, macro_r, macro_f1
    except ImportError:
        # Fallback without sklearn
        total = len(labels)
        if total == 0:
            return 0.0, 0.0, 0.0, 0.0

        acc = sum(p == y for p, y in zip(preds, labels)) / total

        precisions = []
        recalls = []
        f1s = []

        for c in range(num_classes):
            tp = sum(p == c and y == c for p, y in zip(preds, labels))
            fp = sum(p == c and y != c for p, y in zip(preds, labels))
            fn = sum(p != c and y == c for p, y in zip(preds, labels))

            p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0

            precisions.append(p)
            recalls.append(r)
            f1s.append(f)

        macro_p = sum(precisions) / num_classes if num_classes > 0 else 0.0
        macro_r = sum(recalls) / num_classes if num_classes > 0 else 0.0
        macro_f1 = sum(f1s) / num_classes if num_classes > 0 else 0.0

        return acc, macro_p, macro_r, macro_f1


def compute_balanced_weights(labels: List[int], num_classes: int) -> np.ndarray:
    """Compute balanced class weights for cross-entropy loss."""
    try:
        from sklearn.utils.class_weight import compute_class_weight

        unique_classes = np.arange(num_classes)
        return compute_class_weight("balanced", classes=unique_classes, y=labels)
    except ImportError:
        counts = Counter(labels)
        total = len(labels)
        weights = np.zeros(num_classes, dtype=np.float32)
        for c in range(num_classes):
            cnt = counts.get(c, 0)
            weights[c] = total / (num_classes * cnt) if cnt > 0 else 1.0
        return weights


def set_seed(seed: int = 42):
    """Set random seed for reproducibility across torch, numpy, and random."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def evaluate_dataloader(
    model: nn.Module,
    dataloader: DataLoader,
    device: torch.device,
    loss_fn: nn.Module,
    num_classes: int,
) -> Tuple[float, float, float, float, float]:
    """Evaluate model on dataloader and compute loss, accuracy, macro precision, recall, and F1."""
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            loss = loss_fn(logits, labels)
            total_loss += loss.item()

            preds = torch.argmax(logits, dim=-1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(labels.cpu().numpy())

    avg_loss = total_loss / max(len(dataloader), 1)
    acc, macro_p, macro_r, macro_f1 = compute_metrics(all_labels, all_preds, num_classes)

    return avg_loss, acc, macro_p, macro_r, macro_f1


def train(
    data_dir: str,
    output_dir: str,
    base_model: str = "distilbert-base-uncased",
    epochs: int = 5,
    batch_size: int = 16,
    learning_rate: float = 3e-5,
    max_seq_len: int = 128,
    weight_decay: float = 0.01,
    seed: int = 42,
    use_class_weights: bool = True,
    patience: int = 2,
):
    """Execute model fine-tuning and artifact export."""
    set_seed(seed)
    os.makedirs(output_dir, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Using device: %s", device)
    if device.type == "cuda":
        logger.info("GPU Name: %s", torch.cuda.get_device_name(0))

    # 1. Load label mapping
    label_map_path = os.path.join(data_dir, "label_mapping.json")
    if not os.path.isfile(label_map_path):
        raise FileNotFoundError(
            f"label_mapping.json not found in '{data_dir}'. Run preprocess.py first."
        )

    with open(label_map_path, "r", encoding="utf-8") as f:
        label_maps = json.load(f)

    id2label = {int(k): v for k, v in label_maps["id2label"].items()}
    label2id = {k: int(v) for k, v in label_maps["label2id"].items()}
    num_labels = len(id2label)
    logger.info("Loaded label mapping: %d classes.", num_labels)

    # 2. Load splits
    train_texts, train_labels = load_split_csv(os.path.join(data_dir, "train.csv"))
    val_texts, val_labels = load_split_csv(os.path.join(data_dir, "val.csv"))

    logger.info("Training samples: %d, Validation samples: %d", len(train_texts), len(val_texts))

    # 3. Setup Tokenizer & Model
    logger.info("Loading base tokenizer and model: %s", base_model)
    tokenizer = AutoTokenizer.from_pretrained(base_model)

    config = AutoConfig.from_pretrained(
        base_model,
        num_labels=num_labels,
        id2label={str(k): v for k, v in id2label.items()},
        label2id=label2id,
    )
    model = AutoModelForSequenceClassification.from_pretrained(base_model, config=config)
    model.to(device)

    # 4. Prepare Datasets & Dataloaders
    train_dataset = SymptomDataset(
        texts=train_texts,
        labels=train_labels,
        tokenizer=tokenizer,
        max_length=max_seq_len,
    )
    val_dataset = SymptomDataset(
        texts=val_texts,
        labels=val_labels,
        tokenizer=tokenizer,
        max_length=max_seq_len,
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        drop_last=False,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
    )

    # 5. Class imbalance weighting
    if use_class_weights:
        weights = compute_balanced_weights(train_labels, num_labels)
        class_weights_tensor = torch.tensor(weights, dtype=torch.float).to(device)
        loss_fn = nn.CrossEntropyLoss(weight=class_weights_tensor)
        logger.info("Applied balanced class weighting for loss calculation.")
    else:
        loss_fn = nn.CrossEntropyLoss()

    # 6. Optimizer & Scheduler
    no_decay = ["bias", "LayerNorm.weight"]
    optimizer_grouped_parameters = [
        {
            "params": [
                p for n, p in model.named_parameters()
                if not any(nd in n for nd in no_decay)
            ],
            "weight_decay": weight_decay,
        },
        {
            "params": [
                p for n, p in model.named_parameters()
                if any(nd in n for nd in no_decay)
            ],
            "weight_decay": 0.0,
        },
    ]
    optimizer = torch.optim.AdamW(optimizer_grouped_parameters, lr=learning_rate)

    total_steps = len(train_loader) * epochs
    warmup_steps = int(0.1 * total_steps)
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_steps,
    )

    # 7. Training Loop with Early Stopping
    logger.info("Starting training: %d epochs, %d total steps...", epochs, total_steps)
    best_val_f1 = -1.0
    best_val_loss = float("inf")
    patience_counter = 0
    history = []

    start_time = time.time()

    for epoch in range(1, epochs + 1):
        epoch_start = time.time()
        model.train()
        total_train_loss = 0.0

        for step, batch in enumerate(train_loader):
            optimizer.zero_grad()

            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            loss = loss_fn(logits, labels)

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

            optimizer.step()
            scheduler.step()

            total_train_loss += loss.item()

        avg_train_loss = total_train_loss / len(train_loader)
        val_loss, val_acc, val_p, val_r, val_f1 = evaluate_dataloader(
            model, val_loader, device, loss_fn, num_labels
        )
        epoch_duration = time.time() - epoch_start

        logger.info(
            "Epoch %d/%d (%.1fs) | Train Loss: %.4f | Val Loss: %.4f | Val Acc: %.4f | Macro F1: %.4f",
            epoch,
            epochs,
            epoch_duration,
            avg_train_loss,
            val_loss,
            val_acc,
            val_f1,
        )

        history.append({
            "epoch": epoch,
            "train_loss": avg_train_loss,
            "val_loss": val_loss,
            "val_accuracy": val_acc,
            "val_macro_precision": val_p,
            "val_macro_recall": val_r,
            "val_macro_f1": val_f1,
        })

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_val_loss = val_loss
            patience_counter = 0
            logger.info("New best Macro F1: %.4f! Saving model checkpoint to %s", val_f1, output_dir)
            model.save_pretrained(output_dir)
            tokenizer.save_pretrained(output_dir)
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info("Early stopping triggered at epoch %d (patience: %d).", epoch, patience)
                break

    total_duration = time.time() - start_time
    logger.info("Training completed in %.1f seconds. Best Val Macro F1: %.4f", total_duration, best_val_f1)

    # 8. Export Label Mapping & Config metadata to output directory
    with open(os.path.join(output_dir, "label_mapping.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "id2label": {str(k): v for k, v in id2label.items()},
                "label2id": label2id,
            },
            f,
            indent=2,
        )

    training_metadata = {
        "base_model": base_model,
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "max_seq_len": max_seq_len,
        "seed": seed,
        "weight_decay": weight_decay,
        "device": str(device),
        "total_duration_sec": round(total_duration, 2),
        "best_val_macro_f1": round(best_val_f1, 4),
        "best_val_loss": round(best_val_loss, 4),
        "num_classes": num_labels,
        "history": history,
    }

    with open(os.path.join(output_dir, "training_config.json"), "w", encoding="utf-8") as f:
        json.dump(training_metadata, f, indent=2)

    logger.info("All model artifacts and training metadata successfully saved to: %s", output_dir)


def main():
    parser = argparse.ArgumentParser(description="Fine-tune DistilBERT on symptom dataset.")
    parser.add_argument("--data_dir", type=str, default="./processed", help="Path to preprocessed data directory")
    parser.add_argument("--output_dir", type=str, default="./models/symptom", help="Output directory for model artifacts")
    parser.add_argument("--base_model", type=str, default="distilbert-base-uncased", help="Base HF model checkpoint")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size")
    parser.add_argument("--learning_rate", type=float, default=3e-5, help="Learning rate")
    parser.add_argument("--max_seq_len", type=int, default=128, help="Maximum token sequence length")
    parser.add_argument("--weight_decay", type=float, default=0.01, help="Weight decay for AdamW")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--no_class_weights", action="store_true", help="Disable class imbalance weighting")
    parser.add_argument("--patience", type=int, default=2, help="Early stopping patience")

    args = parser.parse_args()

    train(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        base_model=args.base_model,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        max_seq_len=args.max_seq_len,
        weight_decay=args.weight_decay,
        seed=args.seed,
        use_class_weights=not args.no_class_weights,
        patience=args.patience,
    )


if __name__ == "__main__":
    main()
