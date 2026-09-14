"""
train.py — DistilBERT Stage 1 Symptom Classification Training Pipeline

Fine-tunes distilbert-base-uncased on DDXPlus (49 pathologies) for patient symptom text.
Designed for Google Colab with mandatory Google Drive persistence.

Features:
- Stage 1 uses ONLY DDXPlus for training (S2D and Kerala are never trained on).
- Target: DDXPlus PATHOLOGY label (49 classes).
- Strict guard: NEVER uses DIFFERENTIAL_DIAGNOSIS or PATHOLOGY as input features.
- Dynamic padding via DataCollatorWithPadding.
- Line offset indexing for memory-efficient streaming of 1M+ JSONL records.
- Comprehensive Google Drive persistence validation prior to training.
- Deep --validate_only preflight mode (in-memory forward pass, zero weights saved).
"""

import argparse
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import random
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
from torch.utils.data import Dataset
from transformers import (
    AutoConfig,
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    EarlyStoppingCallback,
    Trainer,
    TrainingArguments,
    set_seed,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("train_symptom_stage1")

DEFAULT_MODEL_NAME = "distilbert-base-uncased"
NUM_DDX_CLASSES = 49


# ---------------------------------------------------------------------------
# Dataset with Line Offset Indexing for Large JSONL Files
# ---------------------------------------------------------------------------

class JSONLSymptomDataset(Dataset):
    """
    Memory-efficient Dataset for large JSONL symptom classification files.
    Builds a byte-offset index at initialization so large files (>1M records)
    can be read on-demand without exhausting RAM.
    """

    def __init__(
        self,
        jsonl_path: Path,
        tokenizer,
        label2id: Dict[str, int],
        max_length: int = 128,
        max_samples: Optional[int] = None,
    ):
        self.jsonl_path = Path(jsonl_path)
        self.tokenizer = tokenizer
        self.label2id = label2id
        self.max_length = max_length
        self.offsets: List[int] = []

        if not self.jsonl_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {self.jsonl_path}")

        logger.info(f"Indexing line offsets for {self.jsonl_path.name}...")
        t0 = time.time()
        with open(self.jsonl_path, "rb") as f:
            while True:
                offset = f.tell()
                line = f.readline()
                if not line:
                    break
                self.offsets.append(offset)
                if max_samples and len(self.offsets) >= max_samples:
                    break

        elapsed = time.time() - t0
        logger.info(f"Indexed {len(self.offsets):,} records in {elapsed:.2f}s ({self.jsonl_path.name})")

    def __len__(self) -> int:
        return len(self.offsets)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        offset = self.offsets[idx]
        with open(self.jsonl_path, "r", encoding="utf-8") as f:
            f.seek(offset)
            line = f.readline()

        record = json.loads(line)
        text = record["text"].strip()
        label_str = record["label"]

        if label_str not in self.label2id:
            raise KeyError(f"Unknown label '{label_str}' not in label2id mapping.")

        label_id = self.label2id[label_str]

        # Tokenize without static padding — DataCollatorWithPadding handles dynamic batch padding
        encoding = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding=False,
            return_tensors=None,
        )

        encoding["labels"] = label_id
        return encoding


# ---------------------------------------------------------------------------
# Google Drive Persistence Helpers
# ---------------------------------------------------------------------------

def verify_google_drive_mount(mount_path: str = "/content/drive") -> bool:
    """
    Verifies that Google Drive is mounted and writable before training begins.
    Fails immediately if Drive is unavailable to prevent loss of trained weights.
    """
    path = Path(mount_path)
    if not path.exists():
        logger.error(
            f"Google Drive mount path '{mount_path}' does not exist!\n"
            "Please mount Google Drive before training in Google Colab:\n"
            "    from google.colab import drive\n"
            "    drive.mount('/content/drive')"
        )
        return False

    my_drive = path / "MyDrive"
    if not my_drive.exists():
        logger.error(f"'{mount_path}/MyDrive' not found. Ensure Drive is mounted correctly.")
        return False

    test_file = my_drive / ".mediq_drive_write_test"
    try:
        test_file.write_text("mediq_ok", encoding="utf-8")
        test_file.unlink()
        logger.info(f"Google Drive persistence verified and writable at: {my_drive}")
        return True
    except Exception as exc:
        logger.error(f"Google Drive at '{my_drive}' is not writable: {exc}")
        return False


def setup_persistent_directories(drive_root: Path) -> Dict[str, Path]:
    """
    Creates standard persistent directory hierarchy on Google Drive:
    Google Drive/MediQ/training/symptom/stage1/
        ├── runs/
        ├── checkpoints/
        ├── evaluation/
        └── exports/
    """
    dirs = {
        "runs": drive_root / "runs",
        "checkpoints": drive_root / "checkpoints",
        "evaluation": drive_root / "evaluation",
        "exports": drive_root / "exports",
    }
    for name, p in dirs.items():
        p.mkdir(parents=True, exist_ok=True)
        # Verify write test in each target dir
        test_f = p / ".write_test"
        try:
            test_f.write_text("ok", encoding="utf-8")
            test_f.unlink()
        except Exception as exc:
            raise PermissionError(f"Directory {p} is not writable: {exc}")

    logger.info(f"All persistent directories created and verified under: {drive_root}")
    return dirs


# ---------------------------------------------------------------------------
# Label Mapping Helpers
# ---------------------------------------------------------------------------

def load_stage1_label_mapping(label_map_dir: Path) -> Tuple[List[str], Dict[int, str], Dict[str, int]]:
    """
    Loads the exact 49-class Stage 1 mapping from label_mapping directory.
    Checks stage1_label_mapping.json or label_mapping.json.
    """
    stage1_file = label_map_dir / "stage1_label_mapping.json"
    primary_file = label_map_dir / "label_mapping.json"

    if stage1_file.exists():
        with open(stage1_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        classes = data["classes"]
        id2label = {int(k): v for k, v in data["id2label"].items()}
        label2id = {k: int(v) for k, v in data["label2id"].items()}
        return classes, id2label, label2id

    if primary_file.exists():
        with open(primary_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "id2label" in data and "label2id" in data:
            classes = data.get("stage1_classes", [data["id2label"][str(i)] for i in range(len(data["id2label"]))])
            id2label = {int(k): v for k, v in data["id2label"].items()}
            label2id = {k: int(v) for k, v in data["label2id"].items()}
            return classes, id2label, label2id

    raise FileNotFoundError(f"No valid Stage 1 label mapping found in {label_map_dir}")


# ---------------------------------------------------------------------------
# Metrics Computation
# ---------------------------------------------------------------------------

def compute_metrics_fn(eval_pred):
    """Computes genuine multi-class evaluation metrics."""
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)

    try:
        from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

        acc = float(accuracy_score(labels, preds))
        macro_p = float(precision_score(labels, preds, average="macro", zero_division=0))
        macro_r = float(recall_score(labels, preds, average="macro", zero_division=0))
        macro_f1 = float(f1_score(labels, preds, average="macro", zero_division=0))
        weighted_f1 = float(f1_score(labels, preds, average="weighted", zero_division=0))
    except ImportError:
        total = len(labels)
        acc = float(np.sum(preds == labels) / total) if total > 0 else 0.0
        macro_p = macro_r = macro_f1 = weighted_f1 = 0.0

    return {
        "accuracy": acc,
        "macro_precision": macro_p,
        "macro_recall": macro_r,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
    }


# ---------------------------------------------------------------------------
# Preflight Validation
# ---------------------------------------------------------------------------

def run_preflight_validation(
    data_dir: Path,
    model_name: str,
    label_map_dir: Path,
    use_google_drive: bool = False,
    drive_mount_path: str = "/content/drive",
    drive_root: Optional[Path] = None,
) -> bool:
    """
    Performs exhaustive preflight validation without training or saving weights:
      1. Dataset files existence and integrity
      2. Label mapping exactness (49 classes)
      3. Absence of DIFFERENTIAL_DIAGNOSIS or PATHOLOGY in input text
      4. Pretrained tokenizer loading
      5. Pretrained DistilBERT architecture loading
      6. Sample tokenization check
      7. In-memory forward pass check
      8. Dataset record counts
      9. CUDA / compute device check
      10. Google Drive persistence verification (if requested)
    """
    logger.info("=" * 60)
    logger.info("Running MediQ DistilBERT Stage 1 Preflight Validation")
    logger.info("=" * 60)

    # 1. Check dataset files
    ddx_dir = data_dir / "ddxplus"
    train_file = ddx_dir / "train" / "ddx_train.jsonl"
    val_file = ddx_dir / "validate" / "ddx_validate.jsonl"
    test_file = ddx_dir / "test" / "ddx_test.jsonl"

    for p in [train_file, val_file, test_file]:
        if not p.exists():
            logger.error(f"Missing required dataset file: {p}")
            return False
        logger.info(f"Dataset split found: {p} ({p.stat().st_size:,} bytes)")

    # 2. Check labels
    classes, id2label, label2id = load_stage1_label_mapping(label_map_dir)
    if len(classes) != NUM_DDX_CLASSES:
        logger.error(f"Expected {NUM_DDX_CLASSES} classes, found {len(classes)} in {label_map_dir}")
        return False
    logger.info(f"Verified Stage 1 label mapping: {len(classes)} classes")

    # 3. Inspect sample records for forbidden leakage fields
    logger.info("Verifying input features (checking for forbidden fields)...")
    forbidden_terms = ["DIFFERENTIAL_DIAGNOSIS", "PATHOLOGY:"]
    with open(train_file, "r", encoding="utf-8") as f:
        for idx in range(50):
            line = f.readline()
            if not line:
                break
            record = json.loads(line)
            if "text" not in record or "label" not in record:
                logger.error(f"Record {idx} missing 'text' or 'label' key: {record}")
                return False
            for term in forbidden_terms:
                if term in record["text"]:
                    logger.error(f"Forbidden term '{term}' detected in record text!")
                    return False
    logger.info("PASS: Input text contains only presentation/evidence features (no leakage).")

    # 4. Count datasets
    logger.info("Verifying dataset records counts...")
    summary_path = data_dir / "preprocessing_summary.json"
    if summary_path.exists():
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
        counts = summary.get("counts", {})
        logger.info(f"Verified preprocessing summary: {counts}")

    # 5. Tokenizer test
    logger.info(f"Testing tokenizer load: {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    sample_text = "Patient is a 45-year-old Male with acute chest pain radiating to left arm."
    sample_tok = tokenizer(sample_text, return_tensors="pt")
    logger.info(f"PASS: Sample tokenized length: {sample_tok['input_ids'].shape[1]} tokens")

    # 6. Model architecture & in-memory forward pass test
    logger.info(f"Loading pretrained architecture: {model_name} (num_labels={NUM_DDX_CLASSES})...")
    config = AutoConfig.from_pretrained(
        model_name,
        num_labels=NUM_DDX_CLASSES,
        id2label=id2label,
        label2id=label2id,
    )
    model = AutoModelForSequenceClassification.from_pretrained(model_name, config=config)
    model.eval()

    with torch.no_grad():
        outputs = model(**sample_tok)
        logits = outputs.logits
        if logits.shape != (1, NUM_DDX_CLASSES):
            logger.error(f"Unexpected logits shape: {logits.shape}, expected (1, {NUM_DDX_CLASSES})")
            return False
        logger.info(f"PASS: Forward pass successful. Logits shape: {logits.shape}")

    # 7. Hardware check
    cuda_available = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if cuda_available else "CPU"
    logger.info(f"Compute device: {device_name} (CUDA available: {cuda_available})")

    # 8. Google Drive persistence check (if requested)
    if use_google_drive:
        logger.info("Verifying Google Drive persistence requirements...")
        if not verify_google_drive_mount(drive_mount_path):
            logger.error("Preflight Google Drive verification failed: mount path is unavailable or unwritable.")
            return False
        if drive_root:
            setup_persistent_directories(drive_root)
            logger.info(f"PASS: Google Drive directories verified at: {drive_root}")

    logger.info("=" * 60)
    logger.info("PREFLIGHT VALIDATION PASSED. NO TRAINING OCCURRED.")
    logger.info("=" * 60)
    return True


# ---------------------------------------------------------------------------
# Training Orchestrator
# ---------------------------------------------------------------------------

def train(args: argparse.Namespace) -> None:
    """Orchestrates Stage 1 DistilBERT fine-tuning."""
    set_seed(args.seed)

    base_dir = Path(__file__).resolve().parent
    data_dir = Path(args.data_dir) if args.data_dir else base_dir / "processed"
    label_map_dir = data_dir / "label_mapping"

    # Handle Google Drive persistence paths
    if args.google_drive:
        logger.info("Google Drive persistence enabled.")
        if not verify_google_drive_mount(args.drive_mount_path):
            raise RuntimeError(
                f"Google Drive mount path '{args.drive_mount_path}' is not accessible or not writable. "
                "Halting immediately to prevent training without persistent storage."
            )
        drive_root = Path(args.drive_root)
        persistent_dirs = setup_persistent_directories(drive_root)
        output_dir = persistent_dirs["runs"]
        checkpoint_dir = persistent_dirs["checkpoints"]
    else:
        output_dir = Path(args.output_dir) if args.output_dir else base_dir / "runs" / "stage1"
        checkpoint_dir = output_dir / "checkpoints"
        output_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

    # Preflight validation only
    if args.validate_only:
        drive_root_val = Path(args.drive_root) if args.google_drive else None
        success = run_preflight_validation(
            data_dir=data_dir,
            model_name=args.model_name,
            label_map_dir=label_map_dir,
            use_google_drive=args.google_drive,
            drive_mount_path=args.drive_mount_path,
            drive_root=drive_root_val,
        )
        if not success:
            sys.exit(1)
        logger.info("Preflight validation complete. Exiting without training.")
        return

    # Full training execution (Colab GPU runtime)
    logger.info("Loading Stage 1 label mapping...")
    classes, id2label, label2id = load_stage1_label_mapping(label_map_dir)

    logger.info(f"Loading tokenizer: {args.model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    train_file = data_dir / "ddxplus" / "train" / "ddx_train.jsonl"
    val_file = data_dir / "ddxplus" / "validate" / "ddx_validate.jsonl"

    logger.info("Preparing training dataset...")
    train_dataset = JSONLSymptomDataset(
        jsonl_path=train_file,
        tokenizer=tokenizer,
        label2id=label2id,
        max_length=args.max_seq_length,
        max_samples=args.max_train_samples,
    )

    logger.info("Preparing validation dataset...")
    val_dataset = JSONLSymptomDataset(
        jsonl_path=val_file,
        tokenizer=tokenizer,
        label2id=label2id,
        max_length=args.max_seq_length,
        max_samples=args.max_eval_samples,
    )

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    logger.info(f"Initializing model {args.model_name} with {len(classes)} classes...")
    config = AutoConfig.from_pretrained(
        args.model_name,
        num_labels=len(classes),
        id2label=id2label,
        label2id=label2id,
    )
    model = AutoModelForSequenceClassification.from_pretrained(args.model_name, config=config)

    # Setup training arguments
    run_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_output_dir = output_dir / f"run_{run_timestamp}"

    # Auto-detect fp16 support if CUDA available
    use_fp16 = torch.cuda.is_available()

    training_args = TrainingArguments(
        output_dir=str(run_output_dir),
        eval_strategy=args.eval_strategy,
        save_strategy=args.save_strategy,
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        weight_decay=args.weight_decay,
        warmup_ratio=args.warmup_ratio,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        save_total_limit=args.save_total_limit,
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        greater_is_better=True,
        fp16=use_fp16,
        logging_steps=100,
        seed=args.seed,
        report_to="none",
    )

    callbacks = [EarlyStoppingCallback(early_stopping_patience=args.early_stopping_patience)]

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics_fn,
        callbacks=callbacks,
    )

    # Resume checkpoint handling
    checkpoint_to_resume = None
    if args.resume_from_checkpoint:
        checkpoint_to_resume = args.resume_from_checkpoint
        logger.info(f"Resuming training from checkpoint: {checkpoint_to_resume}")

    logger.info("Starting DistilBERT Stage 1 training...")
    trainer.train(resume_from_checkpoint=checkpoint_to_resume)

    # Save best model to persistent checkpoints directory
    best_model_path = checkpoint_dir / "best"
    logger.info(f"Saving best model to persistent directory: {best_model_path}")
    trainer.save_model(str(best_model_path))
    tokenizer.save_pretrained(str(best_model_path))

    # Save explicit label mapping alongside checkpoint
    with open(best_model_path / "label_mapping.json", "w", encoding="utf-8") as f:
        json.dump({"id2label": id2label, "label2id": label2id, "classes": classes}, f, indent=2, ensure_ascii=False)

    logger.info("DistilBERT Stage 1 training completed successfully.")


# ---------------------------------------------------------------------------
# CLI Argument Parser
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DistilBERT Stage 1 Symptom Model Training Pipeline")

    # Mode
    parser.add_argument("--validate_only", action="store_true", help="Run preflight validation checks and exit without training")

    # Model & Data
    parser.add_argument("--model_name", type=str, default=DEFAULT_MODEL_NAME, help="Pretrained model name or path")
    parser.add_argument("--data_dir", type=str, default="", help="Path to processed symptom data directory")
    parser.add_argument("--max_seq_length", type=int, default=128, help="Maximum sequence length")
    parser.add_argument("--max_train_samples", type=int, default=None, help="Limit training samples (for debug/testing)")
    parser.add_argument("--max_eval_samples", type=int, default=None, help="Limit evaluation samples (for debug/testing)")

    # Hyperparameters
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Per-device batch size")
    parser.add_argument("--learning_rate", type=float, default=2e-5, help="Learning rate")
    parser.add_argument("--weight_decay", type=float, default=0.01, help="Weight decay")
    parser.add_argument("--warmup_ratio", type=float, default=0.1, help="Linear warmup ratio")
    parser.add_argument("--gradient_accumulation_steps", type=int, default=1, help="Gradient accumulation steps")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    # Strategies
    parser.add_argument("--eval_strategy", type=str, default="epoch", choices=["no", "steps", "epoch"], help="Evaluation strategy")
    parser.add_argument("--save_strategy", type=str, default="epoch", choices=["no", "steps", "epoch"], help="Save strategy")
    parser.add_argument("--save_total_limit", type=int, default=2, help="Max checkpoints to keep")
    parser.add_argument("--early_stopping_patience", type=int, default=2, help="Early stopping patience")
    parser.add_argument("--resume_from_checkpoint", type=str, default=None, help="Path to checkpoint to resume from")

    # Storage & Google Drive
    parser.add_argument("--output_dir", type=str, default="", help="Local output directory (when not using Google Drive)")
    parser.add_argument("--google_drive", action="store_true", help="Enforce Google Drive persistence")
    parser.add_argument("--drive_root", type=str, default="/content/drive/MyDrive/MediQ/training/symptom/stage1", help="Google Drive root for Stage 1")
    parser.add_argument("--drive_mount_path", type=str, default="/content/drive", help="Colab Google Drive mount point")

    return parser.parse_args()


if __name__ == "__main__":
    cli_args = parse_args()
    train(cli_args)
