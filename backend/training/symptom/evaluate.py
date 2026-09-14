"""
evaluate.py — Comprehensive Evaluation Pipeline for Stage 1 DistilBERT Symptom Model

Evaluates fine-tuned DistilBERT models across official and generalization splits:
1. Official DDXPlus test split (untouched benchmark).
2. Strict Generalization Evaluation (in-memory filtering of train↔test fingerprint overlaps; dynamic count calculation).
3. DDXPlus validation split.
4. Symptom2Disease test split (external evaluation: in-domain vs out-of-label-space reporting).
5. Kerala evaluation split (external evaluation: out-of-label-space reporting).

Persists evaluation metrics directly to Google Drive:
    Google Drive/MediQ/training/symptom/stage1/evaluation/
        ├── official_test_metrics.json
        ├── strict_test_metrics.json
        ├── symptom2disease_metrics.json
        └── kerala_metrics.json

Includes --validate_only mode for non-training preflight checks.
"""

import argparse
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoConfig,
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("evaluate_symptom_stage1")

NUM_DDX_CLASSES = 49


# ---------------------------------------------------------------------------
# In-Memory Evaluation Dataset
# ---------------------------------------------------------------------------

class InMemSymptomEvalDataset(Dataset):
    """Dataset for batched inference during evaluation."""

    def __init__(self, records: List[Dict[str, Any]], tokenizer, label2id: Dict[str, int], max_length: int = 128):
        self.records = records
        self.tokenizer = tokenizer
        self.label2id = label2id
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        rec = self.records[idx]
        text = rec["text"].strip()
        label_str = rec["label"]
        label_id = self.label2id.get(label_str, -1)

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
# Fingerprint & Dataset Loading Helpers
# ---------------------------------------------------------------------------

def load_train_fingerprints(train_jsonl_path: Path) -> Set[str]:
    """
    Dynamically loads all unique input fingerprints from the DDXPlus training split.
    The fingerprint represents canonical patient presentation: age, sex, initial symptom, and positive evidences.
    """
    if not train_jsonl_path.exists():
        raise FileNotFoundError(f"Training dataset not found for fingerprint extraction: {train_jsonl_path}")

    logger.info(f"Dynamically loading train fingerprints from: {train_jsonl_path}...")
    t0 = time.time()
    train_fps: Set[str] = set()
    with open(train_jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            fp = rec.get("input_fingerprint")
            if fp:
                train_fps.add(fp)

    elapsed = time.time() - t0
    logger.info(f"Loaded {len(train_fps):,} unique train fingerprints in {elapsed:.2f}s.")
    return train_fps


def load_records_from_jsonl(jsonl_path: Path) -> List[Dict[str, Any]]:
    """Loads all records from a JSONL file."""
    if not jsonl_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {jsonl_path}")

    records = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


# ---------------------------------------------------------------------------
# Metric Calculations
# ---------------------------------------------------------------------------

def calculate_multiclass_metrics(
    y_true: List[int],
    y_pred: List[int],
    class_names: List[str],
    compute_confusion: bool = True,
) -> Dict[str, Any]:
    """Calculates comprehensive genuine classification metrics."""
    try:
        from sklearn.metrics import (
            accuracy_score,
            classification_report,
            confusion_matrix,
            f1_score,
            precision_score,
            recall_score,
        )

        acc = float(accuracy_score(y_true, y_pred))
        macro_p = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
        macro_r = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
        macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
        weighted_f1 = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))

        report_dict = classification_report(
            y_true,
            y_pred,
            labels=list(range(len(class_names))),
            target_names=class_names,
            output_dict=True,
            zero_division=0,
        )

        metrics: Dict[str, Any] = {
            "accuracy": acc,
            "macro_precision": macro_p,
            "macro_recall": macro_r,
            "macro_f1": macro_f1,
            "weighted_f1": weighted_f1,
            "per_class": {
                name: {
                    "precision": float(report_dict[name]["precision"]),
                    "recall": float(report_dict[name]["recall"]),
                    "f1": float(report_dict[name]["f1-score"]),
                    "support": int(report_dict[name]["support"]),
                }
                for name in class_names
                if name in report_dict
            },
        }

        if compute_confusion:
            cm = confusion_matrix(y_true, y_pred, labels=list(range(len(class_names))))
            metrics["confusion_matrix"] = cm.tolist()

        return metrics
    except ImportError:
        total = len(y_true)
        correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
        acc = float(correct / total) if total > 0 else 0.0
        return {
            "accuracy": acc,
            "macro_precision": 0.0,
            "macro_recall": 0.0,
            "macro_f1": 0.0,
            "weighted_f1": 0.0,
            "note": "scikit-learn not available; partial metrics only",
        }


# ---------------------------------------------------------------------------
# Evaluation Runners
# ---------------------------------------------------------------------------

def run_model_inference(
    model,
    tokenizer,
    records: List[Dict[str, Any]],
    label2id: Dict[str, int],
    batch_size: int = 64,
    device: Optional[torch.device] = None,
    max_length: int = 128,
) -> Tuple[List[int], List[int], List[List[float]]]:
    """Runs batched inference over a list of records under torch.no_grad()."""
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model.to(device)
    model.eval()

    dataset = InMemSymptomEvalDataset(records, tokenizer, label2id, max_length=max_length)
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False, collate_fn=data_collator)

    all_preds: List[int] = []
    all_labels: List[int] = []
    all_probs: List[List[float]] = []

    with torch.no_grad():
        for batch in dataloader:
            labels = batch.pop("labels").tolist()
            batch = {k: v.to(device) for k, v in batch.items()}
            outputs = model(**batch)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1).cpu().numpy()
            preds = np.argmax(probs, axis=-1).tolist()

            all_preds.extend(preds)
            all_labels.extend(labels)
            all_probs.extend(probs.tolist())

    return all_labels, all_preds, all_probs


def evaluate_ddxplus_official_test(
    model,
    tokenizer,
    test_records: List[Dict[str, Any]],
    classes: List[str],
    label2id: Dict[str, int],
    output_dir: Path,
    batch_size: int = 64,
    device: Optional[torch.device] = None,
) -> Dict[str, Any]:
    """Evaluates untouched official DDXPlus test split."""
    logger.info(f"Evaluating Official DDXPlus Test Split ({len(test_records):,} records)...")
    labels, preds, _ = run_model_inference(model, tokenizer, test_records, label2id, batch_size, device)

    metrics = calculate_multiclass_metrics(labels, preds, classes)
    results = {
        "evaluation_name": "Official DDXPlus Test Evaluation",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_samples": len(test_records),
        "classes_count": len(classes),
        "metrics": metrics,
    }

    out_file = output_dir / "official_test_metrics.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved official test metrics to: {out_file}")
    logger.info(f"Official Test Accuracy: {metrics['accuracy']:.4f} | Macro F1: {metrics['macro_f1']:.4f}")
    return results


def evaluate_ddxplus_strict_test(
    model,
    tokenizer,
    test_records: List[Dict[str, Any]],
    train_fingerprints: Set[str],
    classes: List[str],
    label2id: Dict[str, int],
    output_dir: Path,
    batch_size: int = 64,
    device: Optional[torch.device] = None,
) -> Dict[str, Any]:
    """
    Evaluates DDXPlus test split with known train↔test exact fingerprint overlaps excluded IN MEMORY.
    The official test file is NEVER modified. The count is calculated dynamically from the actual data.
    """
    logger.info("Executing Strict Generalization Evaluation (in-memory overlap exclusion)...")
    filtered_records = []
    overlap_count = 0

    for rec in test_records:
        fp = rec.get("input_fingerprint")
        if fp and fp in train_fingerprints:
            overlap_count += 1
        else:
            filtered_records.append(rec)

    strict_count = len(filtered_records)
    logger.info(
        f"Official test samples: {len(test_records):,} | "
        f"Train overlap filtered: {overlap_count:,} | "
        f"Strict Generalization samples: {strict_count:,}"
    )

    labels, preds, _ = run_model_inference(model, tokenizer, filtered_records, label2id, batch_size, device)

    metrics = calculate_multiclass_metrics(labels, preds, classes)
    results = {
        "evaluation_name": "Strict Generalization Evaluation",
        "description": "DDXPlus official test with train↔test exact symptom fingerprints excluded in-memory",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "official_test_total": len(test_records),
        "filtered_train_overlap_count": overlap_count,
        "evaluated_strict_samples": strict_count,
        "classes_count": len(classes),
        "metrics": metrics,
    }

    out_file = output_dir / "strict_test_metrics.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved strict test metrics to: {out_file}")
    logger.info(f"Strict Generalization Accuracy: {metrics['accuracy']:.4f} | Macro F1: {metrics['macro_f1']:.4f}")
    return results


def evaluate_symptom2disease_external(
    model,
    tokenizer,
    s2d_records: List[Dict[str, Any]],
    classes: List[str],
    label2id: Dict[str, int],
    output_dir: Path,
    batch_size: int = 64,
    device: Optional[torch.device] = None,
) -> Dict[str, Any]:
    """
    External evaluation on the Symptom2Disease test set (119 records, 24 classes).
    Distinguishes between in-label-space classes (Pneumonia, GERD) and out-of-label-space classes.
    """
    logger.info(f"Evaluating external Symptom2Disease test set ({len(s2d_records):,} records)...")

    in_domain_records = []
    out_of_domain_records = []
    class_set = set(classes)

    for rec in s2d_records:
        if rec["label"] in class_set:
            in_domain_records.append(rec)
        else:
            out_of_domain_records.append(rec)

    # In-domain metrics (Pneumonia and GERD)
    in_domain_metrics = None
    if in_domain_records:
        labels, preds, _ = run_model_inference(model, tokenizer, in_domain_records, label2id, batch_size, device)
        in_domain_metrics = calculate_multiclass_metrics(labels, preds, classes, compute_confusion=False)

    # Out-of-domain predictions analysis (what did Stage 1 model predict?)
    out_preds_summary: Dict[str, int] = {}
    if out_of_domain_records:
        _, out_preds, _ = run_model_inference(model, tokenizer, out_of_domain_records, label2id, batch_size, device)
        for pred_id in out_preds:
            pred_name = classes[pred_id]
            out_preds_summary[pred_name] = out_preds_summary.get(pred_name, 0) + 1

    out_classes = sorted(list(set(r["label"] for r in out_of_domain_records)))

    results = {
        "evaluation_name": "External Symptom2Disease Test Evaluation",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_samples": len(s2d_records),
        "in_label_space": {
            "classes": ["GERD", "Pneumonia"],
            "sample_count": len(in_domain_records),
            "metrics": in_domain_metrics,
        },
        "out_of_label_space": {
            "classes_count": len(out_classes),
            "classes": out_classes,
            "sample_count": len(out_of_domain_records),
            "stage1_assigned_predictions": out_preds_summary,
        },
    }

    out_file = output_dir / "symptom2disease_metrics.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved Symptom2Disease external metrics to: {out_file}")
    return results


def evaluate_kerala_external(
    model,
    tokenizer,
    kerala_records: List[Dict[str, Any]],
    classes: List[str],
    label2id: Dict[str, int],
    output_dir: Path,
    batch_size: int = 64,
    device: Optional[torch.device] = None,
) -> Dict[str, Any]:
    """
    External evaluation on the Kerala regional evaluation set (24 records: Chikungunya, Leptospirosis, Nipah).
    All labels are outside Stage 1 label space; cleanly reports distribution without crashing or silent mapping.
    """
    logger.info(f"Evaluating external Kerala evaluation set ({len(kerala_records):,} records)...")

    _, preds, _ = run_model_inference(model, tokenizer, kerala_records, label2id, batch_size, device)

    assigned_predictions: Dict[str, int] = {}
    for pred_id in preds:
        pred_name = classes[pred_id]
        assigned_predictions[pred_name] = assigned_predictions.get(pred_name, 0) + 1

    unique_kerala_labels = sorted(list(set(r["label"] for r in kerala_records)))

    results = {
        "evaluation_name": "External Kerala Evaluation",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_samples": len(kerala_records),
        "in_label_space_samples": 0,
        "out_of_label_space_classes": unique_kerala_labels,
        "note": "Kerala diseases (Chikungunya, Leptospirosis, Nipah) are outside Stage 1 49-class label space.",
        "stage1_assigned_predictions": assigned_predictions,
    }

    out_file = output_dir / "kerala_metrics.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved Kerala external metrics to: {out_file}")
    return results


# ---------------------------------------------------------------------------
# Preflight Validation for Evaluation
# ---------------------------------------------------------------------------

def run_eval_preflight(data_dir: Path, label_map_dir: Path) -> bool:
    """Tests evaluation data loading, fingerprint logic, and metric math without trained weights."""
    logger.info("=" * 60)
    logger.info("Running Evaluation Pipeline Preflight Validation")
    logger.info("=" * 60)

    # 1. Check label mapping
    from train import load_stage1_label_mapping
    classes, id2label, label2id = load_stage1_label_mapping(label_map_dir)
    logger.info(f"Loaded {len(classes)} Stage 1 classes.")

    # 2. Check dataset files
    train_file = data_dir / "ddxplus" / "train" / "ddx_train.jsonl"
    test_file = data_dir / "ddxplus" / "test" / "ddx_test.jsonl"
    s2d_file = data_dir / "symptom2disease" / "test" / "s2d_test.jsonl"
    kerala_file = data_dir / "kerala" / "evaluation" / "kerala_eval.jsonl"

    for p in [train_file, test_file, s2d_file, kerala_file]:
        if not p.exists():
            logger.error(f"Required dataset file missing: {p}")
            return False
        logger.info(f"Dataset split found: {p.name}")

    # 3. Test dynamic fingerprint loading
    logger.info("Testing dynamic fingerprint extraction (sample of train)...")
    sample_fps: Set[str] = set()
    with open(train_file, "r", encoding="utf-8") as f:
        for idx in range(1000):
            line = f.readline()
            if not line:
                break
            sample_fps.add(json.loads(line)["input_fingerprint"])
    logger.info(f"PASS: Dynamically extracted {len(sample_fps)} sample train fingerprints.")

    # 4. Test metric computation on synthetic predictions
    y_true = [0, 1, 2, 3, 0, 1]
    y_pred = [0, 1, 2, 0, 0, 1]
    metrics = calculate_multiclass_metrics(y_true, y_pred, classes[:4], compute_confusion=False)
    if "accuracy" not in metrics or "macro_f1" not in metrics:
        logger.error("Metric calculation test failed.")
        return False
    logger.info(f"PASS: Metric calculation verified (synthetic accuracy: {metrics['accuracy']:.2f}).")

    logger.info("=" * 60)
    logger.info("EVALUATION PREFLIGHT PASSED. NO METRICS FABRICATED.")
    logger.info("=" * 60)
    return True


# ---------------------------------------------------------------------------
# CLI Argument Parser & Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DistilBERT Stage 1 Evaluation Pipeline")

    # Mode
    parser.add_argument("--validate_only", action="store_true", help="Run evaluation preflight check and exit")

    # Model & Data
    parser.add_argument("--checkpoint", type=str, default="", help="Path to trained model checkpoint folder")
    parser.add_argument("--data_dir", type=str, default="", help="Path to processed symptom data directory")
    parser.add_argument("--split", type=str, default="all", choices=["validate", "test", "strict_test", "s2d", "kerala", "all"], help="Evaluation split to run")
    parser.add_argument("--batch_size", type=int, default=64, help="Evaluation batch size")
    parser.add_argument("--max_seq_length", type=int, default=128, help="Maximum sequence length")

    # Storage & Google Drive
    parser.add_argument("--output_dir", type=str, default="", help="Directory to save evaluation JSON files")
    parser.add_argument("--google_drive", action="store_true", help="Use persistent Google Drive evaluation directory")
    parser.add_argument("--drive_root", type=str, default="/content/drive/MyDrive/MediQ/training/symptom/stage1", help="Google Drive Stage 1 root")
    parser.add_argument("--drive_mount_path", type=str, default="/content/drive", help="Colab Google Drive mount point")

    return parser.parse_args()


def main():
    args = parse_args()

    base_dir = Path(__file__).resolve().parent
    data_dir = Path(args.data_dir) if args.data_dir else base_dir / "processed"
    label_map_dir = data_dir / "label_mapping"

    # Preflight validation only
    if args.validate_only:
        success = run_eval_preflight(data_dir, label_map_dir)
        if not success:
            sys.exit(1)
        return

    # Checkpoint resolution
    if not args.checkpoint:
        # Default to Drive if flag set, else local
        if args.google_drive:
            args.checkpoint = str(Path(args.drive_root) / "checkpoints" / "best")
        else:
            args.checkpoint = str(base_dir / "runs" / "stage1" / "checkpoints" / "best")

    checkpoint_path = Path(args.checkpoint)
    if not checkpoint_path.exists():
        logger.error(
            f"Checkpoint directory not found at: {checkpoint_path}\n"
            "Evaluation requires a genuinely trained model checkpoint.\n"
            "Cannot evaluate without weights (no metrics fabricated)."
        )
        sys.exit(1)

    # Output directory resolution
    if args.google_drive:
        output_dir = Path(args.drive_root) / "evaluation"
    elif args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = base_dir / "evaluation" / "stage1"

    output_dir.mkdir(parents=True, exist_ok=True)

    from train import load_stage1_label_mapping
    classes, id2label, label2id = load_stage1_label_mapping(label_map_dir)

    logger.info(f"Loading checkpoint from: {checkpoint_path}...")
    tokenizer = AutoTokenizer.from_pretrained(str(checkpoint_path))
    model = AutoModelForSequenceClassification.from_pretrained(str(checkpoint_path))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Evaluation compute device: {device}")

    # Run evaluations based on selected split
    run_all = args.split == "all"

    # Test splits (Official and Strict)
    if run_all or args.split in ("test", "strict_test"):
        test_file = data_dir / "ddxplus" / "test" / "ddx_test.jsonl"
        test_records = load_records_from_jsonl(test_file)

        if run_all or args.split == "test":
            evaluate_ddxplus_official_test(
                model, tokenizer, test_records, classes, label2id, output_dir, args.batch_size, device
            )

        if run_all or args.split == "strict_test":
            train_file = data_dir / "ddxplus" / "train" / "ddx_train.jsonl"
            train_fps = load_train_fingerprints(train_file)
            evaluate_ddxplus_strict_test(
                model, tokenizer, test_records, train_fps, classes, label2id, output_dir, args.batch_size, device
            )

    # Validation split
    if run_all or args.split == "validate":
        val_file = data_dir / "ddxplus" / "validate" / "ddx_validate.jsonl"
        val_records = load_records_from_jsonl(val_file)
        logger.info(f"Evaluating validation split ({len(val_records):,} records)...")
        labels, preds, _ = run_model_inference(model, tokenizer, val_records, label2id, args.batch_size, device)
        val_metrics = calculate_multiclass_metrics(labels, preds, classes)
        val_results = {
            "evaluation_name": "DDXPlus Validation Split",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "total_samples": len(val_records),
            "metrics": val_metrics,
        }
        with open(output_dir / "validation_metrics.json", "w", encoding="utf-8") as f:
            json.dump(val_results, f, indent=2)
        logger.info(f"Validation Accuracy: {val_metrics['accuracy']:.4f} | Macro F1: {val_metrics['macro_f1']:.4f}")

    # Symptom2Disease external
    if run_all or args.split == "s2d":
        s2d_file = data_dir / "symptom2disease" / "test" / "s2d_test.jsonl"
        s2d_records = load_records_from_jsonl(s2d_file)
        evaluate_symptom2disease_external(
            model, tokenizer, s2d_records, classes, label2id, output_dir, args.batch_size, device
        )

    # Kerala external
    if run_all or args.split == "kerala":
        kerala_file = data_dir / "kerala" / "evaluation" / "kerala_eval.jsonl"
        kerala_records = load_records_from_jsonl(kerala_file)
        evaluate_kerala_external(
            model, tokenizer, kerala_records, classes, label2id, output_dir, args.batch_size, device
        )

    logger.info(f"All requested evaluations completed. Results saved in: {output_dir}")


if __name__ == "__main__":
    main()
