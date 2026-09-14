"""
evaluate.py — MediQ YOLOv8 Model Evaluation Pipeline (Dual-Domain: Skin & Eye)

Evaluates trained YOLOv8 Nano models on held-out validation and test splits:
  - Reports standard object-detection metrics: Precision, Recall, mAP@50, mAP@50-95.
  - Generates granular per-class breakdown for all verified classes.
  - Never fabricates metrics when weights are absent.
  - Never evaluates on the training set as the primary evaluation result.
  - Supports persistent Google Drive output directories.

Usage Examples:
  # Preflight validation only (no trained weights required):
  python evaluate.py --domain skin --validate_only
  python evaluate.py --domain eye --validate_only

  # Full Evaluation on Test Split after Colab Training:
  python evaluate.py --domain skin --split test
  python evaluate.py --domain eye --split test

  # Evaluate both Validation and Test splits:
  python evaluate.py --domain skin --split all
"""

import argparse
import json
import logging
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional

import yaml

# Ensure local imports work cleanly
sys.path.insert(0, str(Path(__file__).resolve().parent))
from preprocess import HAM10000_CLASSES, EYE_CLASSES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("eval_yolo")


def report_per_class_metrics(results: Any, class_names: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Extracts and logs per-class Precision, Recall, mAP50, and mAP50-95 from Ultralytics val results.
    """
    per_class_report: Dict[str, Dict[str, float]] = {}

    log.info("-" * 75)
    log.info(f"{'Class':<30} {'Precision':<10} {'Recall':<10} {'mAP50':<10} {'mAP50-95':<10}")
    log.info("-" * 75)

    try:
        box = results.box
        p_per_class = box.p if hasattr(box, "p") else []
        r_per_class = box.r if hasattr(box, "r") else []
        ap50_per_class = box.ap50 if hasattr(box, "ap50") else []
        ap_per_class = box.ap if hasattr(box, "ap") else []

        for idx, name in enumerate(class_names):
            p = float(p_per_class[idx]) if idx < len(p_per_class) else 0.0
            r = float(r_per_class[idx]) if idx < len(r_per_class) else 0.0
            ap50 = float(ap50_per_class[idx]) if idx < len(ap50_per_class) else 0.0
            ap = float(ap_per_class[idx]) if idx < len(ap_per_class) else 0.0

            per_class_report[name] = {
                "precision": round(p, 4),
                "recall": round(r, 4),
                "mAP50": round(ap50, 4),
                "mAP50-95": round(ap, 4),
            }
            log.info(f"{name:<30} {p:<10.4f} {r:<10.4f} {ap50:<10.4f} {ap:<10.4f}")

    except Exception as exc:
        log.warning(f"Could not extract fine-grained per-class metrics: {exc}")

    log.info("-" * 75)
    return per_class_report


def evaluate_split(
    model_path: Path,
    data_yaml: Path,
    split: str,
    domain: str,
    imgsz: int = 640,
    batch: int = 16,
    conf: float = 0.25,
    iou: float = 0.7,
    device: str = "",
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Executes YOLOv8 evaluation on a specific split (val or test).
    """
    if split not in ("val", "test"):
        raise ValueError(
            f"Invalid split '{split}'. Must be 'val' or 'test'. "
            "Data leakage constraint: Training set cannot be used for primary evaluation."
        )

    if not model_path.exists():
        raise FileNotFoundError(
            f"[{domain.upper()}] Model checkpoint not found at: {model_path}\n"
            f"Please run training first: python train.py --domain {domain}"
        )

    if not data_yaml.exists():
        raise FileNotFoundError(f"[{domain.upper()}] data.yaml not found at: {data_yaml}")

    try:
        from ultralytics import YOLO
    except ImportError:
        raise ImportError("Ultralytics is required for evaluation. Install with: pip install ultralytics")

    class_names = HAM10000_CLASSES if domain == "skin" else EYE_CLASSES

    log.info(f"=== Evaluating {domain.upper()} Model on '{split}' Split ===")
    log.info(f"  Checkpoint : {model_path}")
    log.info(f"  Config     : {data_yaml}")
    log.info(f"  Classes    : {len(class_names)}")

    model = YOLO(str(model_path))
    results = model.val(
        data=str(data_yaml),
        split=split,
        imgsz=imgsz,
        batch=batch,
        conf=conf,
        iou=iou,
        device=device,
        verbose=True,
    )

    metrics_dict = results.results_dict if hasattr(results, "results_dict") else {}
    overall_metrics = {
        "domain": domain,
        "split": split,
        "model": str(model_path.resolve()),
        "data_yaml": str(data_yaml.resolve()),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "precision": float(metrics_dict.get("metrics/precision(B)", 0.0)),
        "recall": float(metrics_dict.get("metrics/recall(B)", 0.0)),
        "mAP50": float(metrics_dict.get("metrics/mAP50(B)", 0.0)),
        "mAP50-95": float(metrics_dict.get("metrics/mAP50-95(B)", 0.0)),
    }

    log.info(f"Overall Metrics ({split} split):")
    log.info(f"  Precision : {overall_metrics['precision']:.4f}")
    log.info(f"  Recall    : {overall_metrics['recall']:.4f}")
    log.info(f"  mAP50     : {overall_metrics['mAP50']:.4f}")
    log.info(f"  mAP50-95  : {overall_metrics['mAP50-95']:.4f}")

    per_class = report_per_class_metrics(results, class_names)
    overall_metrics["per_class"] = per_class

    # Save to persistent evaluation directory
    target_out_dir = output_dir or model_path.parent.parent / "evaluation"
    target_out_dir.mkdir(parents=True, exist_ok=True)
    out_json = target_out_dir / f"eval_{split}_metrics.json"

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(overall_metrics, f, indent=2)
    log.info(f"Evaluation metrics recorded to: {out_json}")

    return overall_metrics


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="MediQ Dual-Domain YOLOv8 Model Evaluation Pipeline (Skin & Eye)."
    )
    p.add_argument(
        "--domain",
        required=True,
        choices=["skin", "eye"],
        help="Target model domain: 'skin' (HAM10000) or 'eye' (SLID)",
    )
    p.add_argument(
        "--model",
        default=None,
        help="Path to trained model .pt checkpoint (defaults to runs/mediq_<domain>/train/weights/best.pt)",
    )
    p.add_argument(
        "--data",
        default=None,
        help="Path to data.yaml (defaults to datasets/<domain>/processed/data.yaml)",
    )
    p.add_argument(
        "--split",
        default="test",
        choices=["val", "test", "all"],
        help="Split to evaluate: 'val', 'test', or 'all' (default: 'test')",
    )
    p.add_argument("--imgsz", type=int, default=640, help="Image resolution")
    p.add_argument("--batch", type=int, default=16, help="Batch size")
    p.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    p.add_argument("--iou", type=float, default=0.7, help="NMS IoU threshold")
    p.add_argument("--device", default="", help="Device: '', '0', 'cpu'")
    p.add_argument("--output-dir", default=None, help="Directory to save evaluation JSON outputs")
    p.add_argument(
        "--google_drive",
        action="store_true",
        help="Look for model and save evaluation metrics directly to Google Drive",
    )
    p.add_argument(
        "--drive_root",
        default=None,
        help="Root path on Google Drive (default: /content/drive/MyDrive/MediQ/training/image)",
    )
    p.add_argument(
        "--validate_only",
        action="store_true",
        help="Preflight check only without requiring trained model weights",
    )
    return p


def main() -> None:
    args = build_parser().parse_args()
    base_dir = Path(__file__).resolve().parent
    domain = args.domain

    # Resolve data.yaml
    data_yaml = (
        Path(args.data)
        if args.data
        else base_dir / "datasets" / domain / "processed" / "data.yaml"
    )

    # Resolve model path
    if args.model:
        model_path = Path(args.model)
    elif args.google_drive:
        drive_base = Path(args.drive_root or "/content/drive/MyDrive/MediQ/training/image")
        model_path = drive_base / domain / "checkpoints" / f"best_{domain}.pt"
    else:
        model_path = base_dir / "runs" / f"mediq_{domain}" / "train" / "weights" / "best.pt"

    # Preflight validation mode
    if args.validate_only:
        log.info(f"=== Preflight Evaluation Check: {domain.upper()} Domain ===")
        log.info(f"  Configured data.yaml : {data_yaml}")
        log.info(f"  Target model path    : {model_path}")
        log.info(f"  Target splits        : {args.split}")

        if not data_yaml.exists():
            raise FileNotFoundError(f"data.yaml not found at: {data_yaml}")

        with open(data_yaml, "r", encoding="utf-8") as f:
            ydata = yaml.safe_load(f)
        expected_classes = HAM10000_CLASSES if domain == "skin" else EYE_CLASSES
        assert ydata.get("nc") == len(expected_classes), "Class count mismatch in data.yaml"
        assert ydata.get("names") == expected_classes, "Class names mismatch in data.yaml"

        model_status = "EXISTS" if model_path.exists() else "AWAITING_TRAINING (cleanly detected)"
        log.info(f"  Model status         : {model_status}")
        log.info(f"  Classes verified     : {len(expected_classes)} ({expected_classes[:3]}...)")
        log.info("EVALUATION PIPELINE VALIDATION PASSED. Exiting without execution per --validate_only.")
        return

    # Check model presence for actual evaluation
    if not model_path.exists():
        log.error(
            f"Cannot run evaluation: trained model weights not found at: {model_path}\n"
            f"Please run model training in Google Colab first:\n"
            f"    python train.py --domain {domain} --google_drive"
        )
        sys.exit(1)

    splits_to_eval = ["val", "test"] if args.split == "all" else [args.split]
    for s in splits_to_eval:
        evaluate_split(
            model_path=model_path,
            data_yaml=data_yaml,
            split=s,
            domain=domain,
            imgsz=args.imgsz,
            batch=args.batch,
            conf=args.conf,
            iou=args.iou,
            device=args.device,
            output_dir=Path(args.output_dir) if args.output_dir else None,
        )


if __name__ == "__main__":
    main()
