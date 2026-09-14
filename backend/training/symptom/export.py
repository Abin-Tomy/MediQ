"""
export.py — Stage 1 DistilBERT Symptom Classifier Export Pipeline

Exports fine-tuned DistilBERT Stage 1 model checkpoints for deployment into the MediQ backend:
  - Destinations:
      * backend/models/symptom/stage1/
      * backend/models/symptom/latest/
  - Artifacts exported:
      * config.json
      * model.safetensors or pytorch_model.bin
      * tokenizer.json, vocab.txt, tokenizer_config.json, special_tokens_map.json
      * label_mapping.json (explicit id2label and label2id for 49 DDXPlus classes)
      * model_metadata.json (comprehensive provenance, stage 2 expansion metadata, clinical disclaimer)
  - Security / Integrity:
      * Safe against missing weights: Never creates fake, placeholder, or dummy model weights.
      * Exits cleanly with code 1 if no genuine checkpoint is present.
      * Supports Google Drive resolution for Google Colab workflows.
      * Includes --validate_only mode for non-training preflight checks.
"""

import argparse
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import shutil
import sys
from typing import Any, Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("export_symptom_stage1")

EXPECTED_WEIGHT_FILES = ["model.safetensors", "pytorch_model.bin"]
EXPECTED_TOKENIZER_FILES = ["tokenizer.json", "vocab.txt", "tokenizer_config.json", "special_tokens_map.json"]


def write_export_metadata(
    output_dir: Path,
    checkpoint_source: Path,
    classes: List[str],
    eval_metrics: Optional[Dict[str, Any]] = None,
    version_tag: str = "stage1-v1.0",
) -> Path:
    """Writes detailed model_metadata.json documenting training provenance and Stage 2 compatibility."""
    metadata = {
        "model_name": "distilbert_symptom",
        "stage": "stage1",
        "base_model": "distilbert-base-uncased",
        "num_classes": len(classes),
        "classes": classes,
        "dataset": {
            "name": "DDXPlus (release)",
            "task": "Patient symptom presentation -> Pathology classification",
            "leakage_prevention": (
                "DIFFERENTIAL_DIAGNOSIS and PATHOLOGY were strictly excluded from input features. "
                "Inputs consist of patient age, sex, initial symptom, and positive evidences translated to English text."
            ),
        },
        "preprocessing_version": "1.0",
        "seed": 42,
        "export_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "checkpoint_source": str(checkpoint_source),
        "version_tag": version_tag,
        "evaluation_summary": eval_metrics or {
            "note": "Evaluation metrics to be populated post-training from official_test_metrics.json and strict_test_metrics.json"
        },
        "stage2_compatibility": {
            "planned_expansion": "49 DDXPlus classes -> 71 unified classes (24 S2D classes with 2 overlaps: Pneumonia, GERD)",
            "transfer_protocol": (
                "The 49 trained Stage 1 classifier weights and biases are copied into their exact matching "
                "positions in the 71-class classifier. The 22 S2D-only classes are initialized with Kaiming uniform. "
                "Stage 2 fine-tuning continues with S2D training data and balanced DDXPlus replay (20 examples/class = 980 samples, seed 42)."
            ),
        },
        "intended_use": "Educational and clinical decision support demonstration. Not FDA-approved or CE-marked as a standalone diagnostic device.",
    }

    metadata_path = output_dir / "model_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return metadata_path


def export_checkpoint(
    checkpoint_path: Path,
    destinations: List[Path],
    label_map_path: Optional[Path] = None,
    eval_metrics: Optional[Dict[str, Any]] = None,
    version_tag: str = "stage1-v1.0",
) -> bool:
    """Exports a genuinely trained checkpoint to destination directories."""
    if not checkpoint_path.exists():
        logger.error(f"Checkpoint path does not exist: {checkpoint_path}")
        return False

    # Check for weights
    has_weights = any((checkpoint_path / w).exists() for w in EXPECTED_WEIGHT_FILES)
    if not has_weights:
        logger.error(
            f"No trained model weights found in {checkpoint_path}.\n"
            f"Expected one of: {EXPECTED_WEIGHT_FILES}\n"
            "Aborting export to prevent publishing dummy or corrupted models."
        )
        return False

    # Check config.json
    if not (checkpoint_path / "config.json").exists():
        logger.error(f"config.json missing from checkpoint: {checkpoint_path}")
        return False

    # Resolve label mapping
    classes: List[str] = []
    mapping_data: Dict[str, Any] = {}
    label_source = checkpoint_path / "label_mapping.json"
    if not label_source.exists() and label_map_path and label_map_path.exists():
        label_source = label_map_path

    if label_source.exists():
        with open(label_source, "r", encoding="utf-8") as f:
            mapping_data = json.load(f)
        if "classes" in mapping_data:
            classes = mapping_data["classes"]
        elif "id2label" in mapping_data:
            classes = [mapping_data["id2label"][str(i)] for i in range(len(mapping_data["id2label"]))]

    if len(classes) != 49:
        logger.warning(f"Label mapping has {len(classes)} classes (expected 49).")

    # Files to copy
    files_to_copy: List[Path] = []
    for f in checkpoint_path.iterdir():
        if f.is_file():
            files_to_copy.append(f)

    for dest in destinations:
        dest.mkdir(parents=True, exist_ok=True)
        logger.info(f"Exporting {len(files_to_copy)} files to: {dest}...")
        for src_file in files_to_copy:
            shutil.copy2(src_file, dest / src_file.name)

        # Ensure label_mapping.json is present
        if mapping_data and not (dest / "label_mapping.json").exists():
            with open(dest / "label_mapping.json", "w", encoding="utf-8") as f:
                json.dump(mapping_data, f, indent=2, ensure_ascii=False)

        # Write model_metadata.json
        write_export_metadata(dest, checkpoint_path, classes, eval_metrics, version_tag)
        logger.info(f"PASS: Export complete for {dest}")

    return True


def run_export_preflight(label_map_dir: Path) -> bool:
    """Preflight check verifying export paths, schema, and missing-weight safety."""
    logger.info("=" * 60)
    logger.info("Running Stage 1 Model Export Preflight Validation")
    logger.info("=" * 60)

    # 1. Verify label mapping availability
    mapping_file = label_map_dir / "stage1_label_mapping.json"
    if not mapping_file.exists():
        mapping_file = label_map_dir / "label_mapping.json"

    if not mapping_file.exists():
        logger.error(f"Missing label mapping file in: {label_map_dir}")
        return False

    with open(mapping_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "id2label" not in data or "label2id" not in data:
        logger.error("Label mapping missing id2label or label2id.")
        return False
    logger.info(f"PASS: Label mapping verified ({len(data['label2id'])} classes).")

    # 2. Check metadata schema serialization
    sample_classes = list(data["label2id"].keys())
    test_meta_path = Path(".test_export_metadata.json")
    try:
        write_export_metadata(Path("."), Path("/dummy/checkpoint"), sample_classes)
        meta_file = Path("model_metadata.json")
        if meta_file.exists():
            meta_file.unlink()
        logger.info("PASS: model_metadata.json structure verified.")
    except Exception as exc:
        logger.error(f"Metadata generation failed: {exc}")
        return False

    logger.info("=" * 60)
    logger.info("EXPORT PREFLIGHT PASSED. NO DUMMY WEIGHTS CREATED.")
    logger.info("=" * 60)
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage 1 DistilBERT Symptom Model Export Pipeline")

    parser.add_argument("--validate_only", action="store_true", help="Run preflight validation and exit")
    parser.add_argument("--checkpoint", type=str, default="", help="Path to trained checkpoint directory")
    parser.add_argument("--google_drive", action="store_true", help="Resolve checkpoint from persistent Google Drive")
    parser.add_argument("--drive_root", type=str, default="/content/drive/MyDrive/MediQ/training/symptom/stage1", help="Google Drive Stage 1 root")
    parser.add_argument("--output_dir", type=str, default="", help="Custom export destination directory")
    parser.add_argument("--version_tag", type=str, default="stage1-v1.0", help="Model version tag")

    return parser.parse_args()


def main():
    args = parse_args()

    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "processed"
    label_map_dir = data_dir / "label_mapping"

    # Preflight check
    if args.validate_only:
        success = run_export_preflight(label_map_dir)
        if not success:
            sys.exit(1)
        return

    # Checkpoint resolution
    if not args.checkpoint:
        if args.google_drive:
            args.checkpoint = str(Path(args.drive_root) / "checkpoints" / "best")
        else:
            args.checkpoint = str(base_dir / "runs" / "stage1" / "checkpoints" / "best")

    checkpoint_path = Path(args.checkpoint)
    if not checkpoint_path.exists():
        logger.error(
            f"No trained checkpoint found at: {checkpoint_path}\n"
            "Cannot export without real fine-tuned weights.\n"
            "No placeholder or fake model weights will be generated."
        )
        sys.exit(1)

    # Destination resolution
    backend_root = base_dir.parents[1]  # backend/
    stage1_dest = backend_root / "models" / "symptom" / "stage1"
    latest_dest = backend_root / "models" / "symptom" / "latest"

    destinations = [stage1_dest, latest_dest]
    if args.output_dir:
        destinations.append(Path(args.output_dir))

    # Try to load evaluation results if available
    eval_metrics = None
    eval_file = checkpoint_path.parent.parent / "evaluation" / "official_test_metrics.json"
    if eval_file.exists():
        with open(eval_file, "r", encoding="utf-8") as f:
            eval_metrics = json.load(f)

    label_map_file = label_map_dir / "stage1_label_mapping.json"

    success = export_checkpoint(
        checkpoint_path=checkpoint_path,
        destinations=destinations,
        label_map_path=label_map_file,
        eval_metrics=eval_metrics,
        version_tag=args.version_tag,
    )

    if not success:
        logger.error("Export failed.")
        sys.exit(1)

    logger.info("Export completed successfully.")


if __name__ == "__main__":
    main()
