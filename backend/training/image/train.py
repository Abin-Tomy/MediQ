"""
train.py — MediQ Production YOLOv8 Nano Training Pipeline (Dual-Domain: Skin & Eye)

Fine-tunes specialized YOLOv8 Nano detection models for:
  1. Skin Condition Model: HAM10000 7 diagnostic categories (akiec, bcc, bkl, df, mel, nv, vasc)
  2. Eye Lesion Model   : SLID Anterior-Eye 14 verified lesion classes

Designed for execution in Google Colab with GPU acceleration and persistent Google Drive storage.

Usage Examples:
  # Preflight validation only (no training, no GPU required, no weight downloads):
  python train.py --domain skin --validate_only
  python train.py --domain eye --validate_only

  # Full Colab GPU Training with Google Drive persistence:
  python train.py --domain skin --google_drive --epochs 50 --batch 16
  python train.py --domain eye --google_drive --epochs 50 --batch 16

  # Resume training after runtime interruption:
  python train.py --domain skin --google_drive --resume
"""

import argparse
import json
import logging
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import yaml

# Ensure local imports work cleanly
sys.path.insert(0, str(Path(__file__).resolve().parent))
from preprocess import HAM10000_CLASSES, EYE_CLASSES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("train_yolo")

EXPECTED_SPLITS = ("train", "val", "test")

DEFAULT_CONFIG: Dict[str, Any] = {
    "checkpoint": "yolov8n.pt",   # Base pretrained YOLOv8 Nano weights (downloaded only at training time)
    "imgsz": 640,                 # Input square image resolution
    "epochs": 50,                 # Full training epochs
    "batch": 16,                  # Batch size per device
    "workers": 4,                 # DataLoader worker threads
    "patience": 20,               # Early stopping patience
    "save_period": 5,             # Checkpoint save interval (every N epochs)
    "seed": 42,                   # Deterministic seed for reproducibility
    "lr0": 1e-3,                  # Initial learning rate
    "lrf": 1e-2,                  # Final learning rate factor (cosine decay)
    "weight_decay": 5e-4,
    "warmup_epochs": 3,
    "mosaic": 1.0,                # Mosaic augmentation enabled
    "flipud": 0.0,                # Vertical flip disabled for anatomical consistency
    "fliplr": 0.5,                # Horizontal flip enabled (bilateral symmetry)
}


# ---------------------------------------------------------------------------
# Hardware Device Detection
# ---------------------------------------------------------------------------

def detect_device(requested_device: Optional[str] = None) -> str:
    """
    Detects and reports the execution device (CUDA GPU or CPU).
    Prints GPU device name and memory when available.
    """
    if requested_device and requested_device.strip():
        device_str = requested_device.strip().lower()
        log.info(f"User specified execution device: '{device_str}'")
        return device_str

    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            device_count = torch.cuda.device_count()
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            log.info(f"CUDA GPU detected: {device_name} ({device_count} device(s), {vram_gb:.2f} GB VRAM)")
            return "0"
        else:
            log.info("CUDA not available. Defaulting to CPU.")
            return "cpu"
    except ImportError:
        log.info("PyTorch not yet loaded. Defaulting to CPU fallback.")
        return "cpu"


# ---------------------------------------------------------------------------
# Google Colab & Google Drive Persistence Setup
# ---------------------------------------------------------------------------

def verify_google_drive_mount(mount_path: str = "/content/drive") -> bool:
    """
    Verifies that Google Drive is mounted before initiating Colab training.
    Prevents silent loss of training checkpoints upon runtime disconnect.
    """
    path = Path(mount_path)
    if not path.exists():
        log.error(
            f"Google Drive mount path '{mount_path}' was not found.\n"
            "Please mount Google Drive in Colab before starting training:\n"
            "    from google.colab import drive\n"
            "    drive.mount('/content/drive')"
        )
        return False

    my_drive = path / "MyDrive"
    if not my_drive.exists():
        log.error(f"MyDrive folder not found under {mount_path}.")
        return False

    test_file = my_drive / ".mediq_drive_write_test"
    try:
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        log.info(f"Google Drive mount verified and writable: {my_drive}")
        return True
    except Exception as exc:
        log.error(f"Cannot write to Google Drive at '{my_drive}': {exc}")
        return False


def setup_directories(
    domain: str,
    use_google_drive: bool = False,
    drive_root: Optional[str] = None,
    project_override: Optional[str] = None,
) -> Dict[str, Path]:
    """
    Configures persistent output, checkpoint, evaluation, and export directories.
    Ensures skin and eye models are kept completely isolated.
    """
    base_dir = Path(__file__).resolve().parent

    if use_google_drive:
        root = Path(drive_root or "/content/drive/MyDrive/MediQ/training/image")
        domain_root = root / domain
    elif project_override:
        domain_root = Path(project_override)
    else:
        domain_root = base_dir / "runs" / f"mediq_{domain}"

    dirs = {
        "root": domain_root,
        "runs": domain_root / "runs",
        "checkpoints": domain_root / "checkpoints",
        "evaluation": domain_root / "evaluation",
        "exports": domain_root / "exports",
    }

    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    log.info(f"[{domain.upper()}] Directory hierarchy initialized:")
    for k, v in dirs.items():
        log.info(f"  {k:<12}: {v}")

    return dirs


# ---------------------------------------------------------------------------
# Preflight Dataset Validation (Strict Guardrails)
# ---------------------------------------------------------------------------

def validate_dataset_preflight(domain: str, data_yaml_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Performs rigorous preflight validation of the processed dataset prior to training:
    - Verifies data.yaml exists and is structurally valid.
    - Confirms train, val, and test directories exist.
    - Checks that image and label files exist and match.
    - Verifies class count and class names match exact expected domain taxonomy.
    - Validates label lines for correct YOLO normalized coordinate bounds.
    """
    log.info(f"=== Performing Preflight Dataset Validation: {domain.upper()} ===")
    base_dir = Path(__file__).resolve().parent

    if data_yaml_path is None:
        data_yaml_path = base_dir / "datasets" / domain / "processed" / "data.yaml"
    else:
        data_yaml_path = Path(data_yaml_path)

    if not data_yaml_path.exists():
        raise FileNotFoundError(
            f"[{domain.upper()}] Dataset configuration not found: {data_yaml_path.resolve()}\n"
            f"Run preprocessing first: python preprocess.py --domain {domain}"
        )

    with open(data_yaml_path, "r", encoding="utf-8") as f:
        yaml_data = yaml.safe_load(f)

    expected_classes = HAM10000_CLASSES if domain == "skin" else EYE_CLASSES
    expected_nc = len(expected_classes)

    # 1. Validate YAML schema
    yaml_nc = yaml_data.get("nc")
    yaml_names = yaml_data.get("names")

    if yaml_nc != expected_nc:
        raise ValueError(
            f"[{domain.upper()}] Class count mismatch in data.yaml: expected {expected_nc}, got {yaml_nc}"
        )

    if yaml_names != expected_classes:
        raise ValueError(
            f"[{domain.upper()}] Class names mismatch in data.yaml!\n"
            f"  Expected: {expected_classes}\n"
            f"  Found   : {yaml_names}"
        )

    log.info(f"[{domain.upper()}] data.yaml validated: {yaml_nc} classes match exact verified taxonomy.")

    # 2. Validate split directories and file pairings
    dataset_root = data_yaml_path.parent
    split_counts: Dict[str, Dict[str, int]] = {}
    total_images = 0
    total_labels = 0
    total_boxes = 0

    for split in EXPECTED_SPLITS:
        img_dir = dataset_root / "images" / split
        lbl_dir = dataset_root / "labels" / split

        if not img_dir.exists():
            raise FileNotFoundError(f"[{domain.upper()}] Image directory missing: {img_dir}")
        if not lbl_dir.exists():
            raise FileNotFoundError(f"[{domain.upper()}] Label directory missing: {lbl_dir}")

        # Collect images
        images = list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png"))
        labels = list(lbl_dir.glob("*.txt"))

        if len(images) == 0:
            raise ValueError(f"[{domain.upper()}] Split '{split}' contains 0 images in {img_dir}")
        if len(images) != len(labels):
            raise ValueError(
                f"[{domain.upper()}] Split '{split}' mismatch: {len(images)} images vs {len(labels)} labels"
            )

        boxes_in_split = 0
        negatives_in_split = 0

        for img_p in images:
            lbl_p = lbl_dir / f"{img_p.stem}.txt"
            if not lbl_p.exists():
                raise FileNotFoundError(f"Missing label file for image: {img_p.name}")

            content = lbl_p.read_text(encoding="utf-8").strip()
            if not content:
                negatives_in_split += 1
                continue

            for line_idx, line in enumerate(content.splitlines(), start=1):
                parts = line.strip().split()
                if len(parts) != 5:
                    raise ValueError(f"Malformed label in {lbl_p.name} line {line_idx}: '{line}'")

                cid = int(parts[0])
                xc, yc, w, h = map(float, parts[1:])

                if cid < 0 or cid >= expected_nc:
                    raise ValueError(f"Invalid class ID {cid} in {lbl_p.name} (nc={expected_nc})")
                if not (0.0 <= xc <= 1.0 and 0.0 <= yc <= 1.0):
                    raise ValueError(f"Coordinates outside [0, 1] in {lbl_p.name}: xc={xc}, yc={yc}")
                if not (0.0 < w <= 1.0 and 0.0 < h <= 1.0):
                    raise ValueError(f"Invalid dimensions in {lbl_p.name}: w={w}, h={h}")

                boxes_in_split += 1

        split_counts[split] = {
            "images": len(images),
            "labels": len(labels),
            "boxes": boxes_in_split,
            "negatives": negatives_in_split,
        }
        total_images += len(images)
        total_labels += len(labels)
        total_boxes += boxes_in_split

        log.info(
            f"  Split '{split:<5}': {len(images):,} images, {boxes_in_split:,} bounding boxes, "
            f"{negatives_in_split:,} background images."
        )

    log.info(
        f"[{domain.upper()}] Preflight validation PASSED: "
        f"{total_images:,} images, {total_boxes:,} ground-truth boxes 100% verified."
    )

    return {
        "domain": domain,
        "data_yaml": str(data_yaml_path.resolve()),
        "nc": expected_nc,
        "classes": expected_classes,
        "split_counts": split_counts,
        "total_images": total_images,
        "total_boxes": total_boxes,
    }


# ---------------------------------------------------------------------------
# Training Orchestration
# ---------------------------------------------------------------------------

def run_training(config: Dict[str, Any]) -> None:
    """
    Executes fine-tuning of YOLOv8 Nano on the verified dataset.
    Imports Ultralytics and loads weights strictly when training is invoked.
    """
    domain = config["domain"]
    log.info(f"=== Initializing YOLOv8 Nano Fine-Tuning: {domain.upper()} Domain ===")

    # Step 1: Preflight validation
    validation_info = validate_dataset_preflight(domain, config.get("data"))

    # Step 2: Persistence directory configuration
    dirs = setup_directories(
        domain=domain,
        use_google_drive=config.get("google_drive", False),
        drive_root=config.get("drive_root"),
        project_override=config.get("project"),
    )

    # Step 3: Handle resuming
    resume_flag = config.get("resume", False)
    checkpoint_to_load = config["checkpoint"]
    last_pt = dirs["runs"] / config["name"] / "weights" / "last.pt"

    if resume_flag:
        if last_pt.exists():
            log.info(f"Resuming training from existing checkpoint: {last_pt}")
            checkpoint_to_load = str(last_pt)
        else:
            raise FileNotFoundError(
                f"Cannot resume: checkpoint '{last_pt}' does not exist in run directory.\n"
                f"Check that previous training run '{config['name']}' exists."
            )

    # Step 4: Import Ultralytics and instantiate model
    try:
        from ultralytics import YOLO
    except ImportError:
        raise ImportError("Ultralytics is required for training. Install with: pip install ultralytics")

    device = detect_device(config.get("device"))

    log.info(f"Loading base checkpoint: {checkpoint_to_load}")
    model = YOLO(checkpoint_to_load)

    # Step 5: Save pre-training configuration artifact
    run_config_artifact = dirs["root"] / f"train_{domain}_config.json"
    with open(run_config_artifact, "w", encoding="utf-8") as f:
        json.dump(
            {
                "domain": domain,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "config": {k: str(v) if isinstance(v, Path) else v for k, v in config.items()},
                "validation_info": validation_info,
                "device": device,
            },
            f,
            indent=2,
        )
    log.info(f"Training run configuration recorded: {run_config_artifact}")

    # Step 6: Launch training
    log.info(f"Starting Ultralytics model.train() for {config['epochs']} epochs on {device}...")
    results = model.train(
        data=validation_info["data_yaml"],
        epochs=config["epochs"],
        patience=config["patience"],
        batch=config["batch"],
        imgsz=config["imgsz"],
        workers=config["workers"],
        lr0=config["lr0"],
        lrf=config["lrf"],
        weight_decay=config["weight_decay"],
        warmup_epochs=config["warmup_epochs"],
        mosaic=config["mosaic"],
        flipud=config["flipud"],
        fliplr=config["fliplr"],
        project=str(dirs["runs"]),
        name=config["name"],
        exist_ok=True,
        seed=config["seed"],
        device=device,
        save=True,
        save_period=config["save_period"],
        resume=resume_flag,
        verbose=True,
    )

    # Step 7: Copy best checkpoint to persistent checkpoints directory
    best_weights = dirs["runs"] / config["name"] / "weights" / "best.pt"
    if best_weights.exists():
        persistent_best = dirs["checkpoints"] / f"best_{domain}.pt"
        import shutil
        shutil.copy2(best_weights, persistent_best)
        log.info(f"Best model preserved at persistent checkpoint: {persistent_best}")

    log.info(f"=== {domain.upper()} Training Complete ===")


# ---------------------------------------------------------------------------
# CLI Argument Parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="MediQ Dual-Domain YOLOv8 Nano Training Pipeline (Skin & Eye)."
    )
    p.add_argument(
        "--domain",
        required=True,
        choices=["skin", "eye"],
        help="Target model domain: 'skin' (HAM10000) or 'eye' (SLID)",
    )
    p.add_argument(
        "--data",
        default=None,
        help="Optional override path to data.yaml (defaults to datasets/<domain>/processed/data.yaml)",
    )
    p.add_argument(
        "--checkpoint",
        default=DEFAULT_CONFIG["checkpoint"],
        help="Base pretrained model checkpoint (default: yolov8n.pt)",
    )
    p.add_argument(
        "--epochs",
        type=int,
        default=DEFAULT_CONFIG["epochs"],
        help="Number of training epochs (default: 50)",
    )
    p.add_argument(
        "--batch",
        type=int,
        default=DEFAULT_CONFIG["batch"],
        help="Batch size (default: 16)",
    )
    p.add_argument(
        "--imgsz",
        type=int,
        default=DEFAULT_CONFIG["imgsz"],
        help="Input image resolution (default: 640)",
    )
    p.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_CONFIG["workers"],
        help="DataLoader worker count (default: 4)",
    )
    p.add_argument(
        "--patience",
        type=int,
        default=DEFAULT_CONFIG["patience"],
        help="Early stopping patience epochs (default: 20)",
    )
    p.add_argument(
        "--save_period",
        type=int,
        default=DEFAULT_CONFIG["save_period"],
        help="Checkpoint save frequency in epochs (default: 5)",
    )
    p.add_argument(
        "--lr0",
        type=float,
        default=DEFAULT_CONFIG["lr0"],
        help="Initial learning rate (default: 1e-3)",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_CONFIG["seed"],
        help="Deterministic random seed (default: 42)",
    )
    p.add_argument(
        "--device",
        default="",
        help="Device to run on: '' (auto CUDA/CPU), '0', 'cpu'",
    )
    p.add_argument(
        "--google_drive",
        action="store_true",
        help="Enforce persistent Google Drive storage for runs and checkpoints",
    )
    p.add_argument(
        "--drive_root",
        default=None,
        help="Root path on Google Drive (default: /content/drive/MyDrive/MediQ/training/image)",
    )
    p.add_argument(
        "--project",
        default=None,
        help="Output project directory override",
    )
    p.add_argument(
        "--name",
        default=None,
        help="Experiment name (defaults to 'mediq_skin' or 'mediq_eye')",
    )
    p.add_argument(
        "--resume",
        action="store_true",
        help="Resume training from last.pt checkpoint in the run directory",
    )
    p.add_argument(
        "--validate_only",
        action="store_true",
        help="Execute preflight dataset & environment validation only (NO training, NO weight downloads)",
    )
    return p


def main() -> None:
    args = build_parser().parse_args()

    domain = args.domain
    experiment_name = args.name or f"mediq_{domain}"

    # Handle --validate_only
    if args.validate_only:
        log.info(f"=== Preflight Validation Mode: {domain.upper()} Domain ===")
        device = detect_device(args.device)
        validation_info = validate_dataset_preflight(domain, args.data)
        log.info(f"Target execution device: {device}")
        log.info(f"Target checkpoint: {args.checkpoint}")
        log.info(f"Target epochs: {args.epochs}, batch: {args.batch}, imgsz: {args.imgsz}")
        log.info(f"Deterministic seed: {args.seed}")
        log.info("PREFLIGHT VALIDATION PASSED. Exiting without training per --validate_only.")
        return

    # If Google Drive requested, verify mount first
    if args.google_drive:
        if not verify_google_drive_mount():
            sys.exit(1)

    cfg = {
        **DEFAULT_CONFIG,
        **vars(args),
        "name": experiment_name,
    }

    run_training(cfg)


if __name__ == "__main__":
    main()
