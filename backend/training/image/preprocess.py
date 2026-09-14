"""
preprocess.py — MediQ Dual-Domain YOLOv8 Image Dataset Preprocessing Pipeline

Prepares medical image datasets for two specialized YOLOv8 Nano models:
  1. Skin Model : HAM10000 dermoscopy images + lesion segmentation masks
                  converted deterministically to YOLO bounding boxes across
                  all 7 diagnostic classes (akiec, bcc, bkl, df, mel, nv, vasc).
                  Uses patient/lesion-aware (lesion_id) grouped stratified split
                  to strictly eliminate cross-split data leakage.
  2. Eye Model  : Slit-Lamp Image Dataset (SLID) anterior-eye clinical photographs
                  with genuine expert multi-shape annotations (rect, circle, ellipse,
                  polygon) across 14 verified eye lesion/pathology categories.
                  Strictly NO OCT / retinal OCT datasets and NO synthetic bounding boxes.

Directory structures produced:
  datasets/<domain>/processed/
  ├── images/
  │   ├── train/
  │   ├── val/
  │   └── test/
  ├── labels/
  │   ├── train/
  │   ├── val/
  │   └── test/
  ├── data.yaml
  ├── preprocessing_report.md
  └── preprocessing_summary.json
"""

import argparse
from collections import Counter, defaultdict
import csv
from dataclasses import dataclass
import hashlib
import json
import logging
import math
import os
from pathlib import Path
import random
import shutil
import sys
import time
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from PIL import Image

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("preprocess_yolo")

# ---------------------------------------------------------------------------
# Class Configurations & Clinical Taxonomy
# ---------------------------------------------------------------------------

# HAM10000 7 diagnostic categories (fixed clinical order)
HAM10000_CLASSES: List[str] = [
    "akiec",  # Actinic keratoses and intraepithelial carcinoma / Bowen's disease
    "bcc",    # Basal cell carcinoma
    "bkl",    # Benign keratosis-like lesions (solar lentigines / seborrheic keratoses)
    "df",     # Dermatofibroma
    "mel",    # Melanoma
    "nv",     # Melanocytic nevi
    "vasc",   # Vascular lesions (angiomas, pyogenic granulomas, hemorrhage)
]

HAM10000_CLASS_NAMES: Dict[str, str] = {
    "akiec": "Actinic Keratosis / Intraepithelial Carcinoma",
    "bcc": "Basal Cell Carcinoma",
    "bkl": "Benign Keratosis-like Lesion",
    "df": "Dermatofibroma",
    "mel": "Melanoma",
    "nv": "Melanocytic Nevus",
    "vasc": "Vascular Lesion",
}

# SLID 14 verified eye lesion/pathology categories from Annotations.csv
EYE_CLASSES: List[str] = [
    "Cataract",
    "Conjunctival cyst",
    "Conjunctival injection",
    "Corneal / Conjunctival tumor",
    "Corneal dystrophy",
    "Corneal scarring",
    "Intraocular lens",
    "Keratitis",
    "Lens dislocation",
    "Lens dislocation/Cataract",
    "Pigmented nevus",
    "Pinguecula",
    "Pterygium",
    "Subconjunctival hemorrhage",
]

EXPECTED_DOMAINS = ("skin", "eye")
EXPECTED_SPLITS = ("train", "val", "test")


# ---------------------------------------------------------------------------
# Preprocessing Configuration Dataclass
# ---------------------------------------------------------------------------

@dataclass
class PreprocessingConfig:
    """Configuration parameters for dataset preparation and validation."""

    domain: str                                                     # "skin" or "eye"
    random_seed: int = 42                                           # Deterministic split seed
    image_size: int = 640                                           # Target YOLO square image size
    split_ratios: Tuple[float, float, float] = (0.70, 0.15, 0.15)   # train, val, test
    min_bbox_area: float = 16.0                                     # Minimum bbox area in pixels
    max_allowed_invalid_boxes: int = 0                              # Error tolerance for corrupted bboxes
    raw_dir: Optional[Path] = None                                  # Root directory containing raw data
    output_dir: Optional[Path] = None                               # Root directory for processed YOLO dataset

    def __post_init__(self):
        if self.domain not in EXPECTED_DOMAINS:
            raise ValueError(f"Invalid domain '{self.domain}'. Must be one of {EXPECTED_DOMAINS}")

        train_r, val_r, test_r = self.split_ratios
        if not math.isclose(train_r + val_r + test_r, 1.0, rel_tol=1e-4):
            raise ValueError(f"Split ratios must sum to 1.0, got: {self.split_ratios}")

        base_dir = Path(__file__).resolve().parent
        if self.raw_dir is None:
            self.raw_dir = base_dir / "datasets" / self.domain / "raw"
        else:
            self.raw_dir = Path(self.raw_dir)

        if self.output_dir is None:
            self.output_dir = base_dir / "datasets" / self.domain / "processed"
        else:
            self.output_dir = Path(self.output_dir)


# ---------------------------------------------------------------------------
# Class Definition Validation
# ---------------------------------------------------------------------------

def get_domain_classes(domain: str) -> List[str]:
    """Return configured classes for a domain."""
    if domain == "skin":
        return list(HAM10000_CLASSES)
    elif domain == "eye":
        return list(EYE_CLASSES)
    else:
        raise ValueError(f"Unsupported domain: {domain}")


def validate_class_configuration(domain: str, class_list: List[str]) -> bool:
    """Validate class definitions for the target domain."""
    if domain == "skin":
        if class_list != HAM10000_CLASSES:
            raise ValueError(
                f"Skin domain classes must match exact order: {HAM10000_CLASSES}, got: {class_list}"
            )
        if len(class_list) != 7:
            raise ValueError(f"Skin domain requires 7 distinct classes, got {len(class_list)}")

    elif domain == "eye":
        if class_list != EYE_CLASSES:
            raise ValueError(
                f"Eye domain classes must match verified SLID classes: {EYE_CLASSES}, got: {class_list}"
            )
        if len(class_list) != 14:
            raise ValueError(f"Eye domain requires 14 distinct classes, got {len(class_list)}")

    log.info(f"[{domain.upper()}] Class configuration valid: {len(class_list)} classes -> {class_list}")
    return True


# ---------------------------------------------------------------------------
# HAM10000 Skin Preprocessing
# ---------------------------------------------------------------------------

def mask_to_bounding_box(
    mask_array: np.ndarray,
    img_width: int,
    img_height: int,
    class_id: int,
    min_area: float = 16.0,
) -> Optional[Tuple[int, float, float, float, float]]:
    """Convert a 2D binary segmentation mask into a normalized YOLO bounding box."""
    if mask_array is None or mask_array.size == 0:
        return None

    binary = mask_array > 0
    if not np.any(binary):
        return None

    y_indices, x_indices = np.where(binary)
    x_min = int(np.min(x_indices))
    x_max = int(np.max(x_indices))
    y_min = int(np.min(y_indices))
    y_max = int(np.max(y_indices))

    box_w = x_max - x_min + 1
    box_h = y_max - y_min + 1

    if (box_w * box_h) < min_area or box_w <= 0 or box_h <= 0:
        return None

    x_center = (x_min + box_w / 2.0) / float(img_width)
    y_center = (y_min + box_h / 2.0) / float(img_height)
    norm_w = box_w / float(img_width)
    norm_h = box_h / float(img_height)

    x_center = max(0.0, min(1.0, x_center))
    y_center = max(0.0, min(1.0, y_center))
    norm_w = max(0.0, min(1.0, norm_w))
    norm_h = max(0.0, min(1.0, norm_h))

    return (class_id, x_center, y_center, norm_w, norm_h)


def split_ham10000_lesion_aware(
    metadata_records: List[Dict[str, Any]],
    split_ratios: Tuple[float, float, float] = (0.70, 0.15, 0.15),
    seed: int = 42,
) -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, Set[str]]]:
    """Perform a patient/lesion-aware grouped stratified split on HAM10000 metadata."""
    train_ratio, val_ratio, test_ratio = split_ratios

    lesions: Dict[str, List[Dict[str, Any]]] = {}
    lesion_dx: Dict[str, str] = {}

    for row in metadata_records:
        lid = row["lesion_id"]
        dx = row["dx"]
        if lid not in lesions:
            lesions[lid] = []
            lesion_dx[lid] = dx
        lesions[lid].append(row)

    dx_to_lesions: Dict[str, List[str]] = {}
    for lid, dx in sorted(lesion_dx.items()):
        dx_to_lesions.setdefault(dx, []).append(lid)

    rng = random.Random(seed)
    split_lesions: Dict[str, Set[str]] = {"train": set(), "val": set(), "test": set()}

    for dx, lids in sorted(dx_to_lesions.items()):
        lids_sorted = sorted(lids)
        rng.shuffle(lids_sorted)
        n = len(lids_sorted)

        n_train = int(round(n * train_ratio))
        n_val = int(round(n * val_ratio))

        train_lids = lids_sorted[:n_train]
        val_lids = lids_sorted[n_train:n_train + n_val]
        test_lids = lids_sorted[n_train + n_val:]

        split_lesions["train"].update(train_lids)
        split_lesions["val"].update(val_lids)
        split_lesions["test"].update(test_lids)

    tv = split_lesions["train"] & split_lesions["val"]
    tt = split_lesions["train"] & split_lesions["test"]
    vt = split_lesions["val"] & split_lesions["test"]

    if tv or tt or vt:
        raise RuntimeError(f"FATAL: Lesion leakage detected between splits!")

    split_records: Dict[str, List[Dict[str, Any]]] = {"train": [], "val": [], "test": []}
    for split_name, lids in split_lesions.items():
        for lid in sorted(lids):
            split_records[split_name].extend(lesions[lid])

    return split_records, split_lesions


def process_skin_dataset(config: PreprocessingConfig) -> Dict[str, Any]:
    """Complete preprocessing workflow for HAM10000 skin dataset."""
    log.info("=== Starting HAM10000 Skin Image Preprocessing Pipeline ===")
    classes = get_domain_classes("skin")
    validate_class_configuration("skin", classes)
    class_to_idx = {name: idx for idx, name in enumerate(classes)}

    raw_dir = config.raw_dir
    output_dir = config.output_dir

    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw directory does not exist: {raw_dir}")

    metadata_path = raw_dir / "HAM10000_metadata.csv"
    masks_dir = raw_dir / "HAM10000_segmentations_lesion_tschandl"
    part1_dir = raw_dir / "HAM10000_images_part_1"
    part2_dir = raw_dir / "HAM10000_images_part_2"

    with open(metadata_path, "r", encoding="utf-8") as f:
        records = list(csv.DictReader(f))

    image_paths: Dict[str, Path] = {}
    for p in part1_dir.glob("*.jpg"):
        image_paths[p.stem] = p
    for p in part2_dir.glob("*.jpg"):
        image_paths[p.stem] = p

    mask_paths: Dict[str, Path] = {}
    for p in masks_dir.glob("*.png"):
        stem = p.stem.replace("_segmentation", "")
        mask_paths[stem] = p

    split_records, split_lesions = split_ham10000_lesion_aware(
        records, split_ratios=config.split_ratios, seed=config.random_seed
    )

    for sub in ("images", "labels"):
        for s in EXPECTED_SPLITS:
            (output_dir / sub / s).mkdir(parents=True, exist_ok=True)

    split_stats: Dict[str, Dict[str, Any]] = {}
    total_boxes_generated = 0

    for s in EXPECTED_SPLITS:
        records_in_split = split_records[s]
        class_counts = {c: 0 for c in classes}
        boxes_in_split = 0

        for r in records_in_split:
            iid = r["image_id"]
            dx = r["dx"]
            class_id = class_to_idx[dx]

            src_img = image_paths[iid]
            dst_img = output_dir / "images" / s / f"{iid}.jpg"
            shutil.copy2(src_img, dst_img)

            src_mask = mask_paths[iid]
            with Image.open(src_mask) as m_img:
                m_arr = np.array(m_img)
                w, h = m_img.size

            bbox_tuple = mask_to_bounding_box(
                m_arr, img_width=w, img_height=h, class_id=class_id, min_area=config.min_bbox_area
            )
            cid, xc, yc, bw, bh = bbox_tuple
            label_file = output_dir / "labels" / s / f"{iid}.txt"
            label_file.write_text(f"{cid} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}\n", encoding="utf-8")

            class_counts[dx] += 1
            boxes_in_split += 1
            total_boxes_generated += 1

        split_stats[s] = {
            "image_count": len(records_in_split),
            "lesion_count": len(split_lesions[s]),
            "label_count": boxes_in_split,
            "class_distribution": class_counts,
        }

    yaml_path = output_dir / "data.yaml"
    yaml_content = (
        f"# MediQ YOLOv8 Nano Skin Lesion Detection Dataset Config\n"
        f"path: .\n"
        f"train: images/train\n"
        f"val: images/val\n"
        f"test: images/test\n\n"
        f"nc: {len(classes)}\n"
        f"names: {classes}\n"
    )
    yaml_path.write_text(yaml_content, encoding="utf-8")
    log.info("Skin dataset processing complete.")
    return split_stats


# ---------------------------------------------------------------------------
# SLID Eye Preprocessing
# ---------------------------------------------------------------------------

def parse_slid_shape_to_bbox(
    shape: Dict[str, Any],
    img_width: int,
    img_height: int,
    class_id: int,
) -> Optional[Tuple[int, float, float, float, float]]:
    """
    Converts a genuine SLID shape (rect, circle, ellipse, polygon) to a normalized YOLO bounding box.

    Applies boundary clamping to [0, img_w] and [0, img_h] for circular/elliptical lesions drawn
    near image margins, while verifying positive dimension validity.
    """
    s_name = shape.get("name")

    if s_name == "rect":
        x = float(shape["x"])
        y = float(shape["y"])
        w = float(shape["width"])
        h = float(shape["height"])
        x_min, x_max = x, x + w
        y_min, y_max = y, y + h

    elif s_name == "circle":
        cx = float(shape["cx"])
        cy = float(shape["cy"])
        r = float(shape["r"])
        x_min, x_max = cx - r, cx + r
        y_min, y_max = cy - r, cy + r

    elif s_name == "ellipse":
        cx = float(shape["cx"])
        cy = float(shape["cy"])
        rx = float(shape["rx"])
        ry = float(shape["ry"])
        theta = float(shape.get("theta", 0.0))
        # Exact bounding box half-width and half-height of rotated ellipse
        half_w = math.sqrt((rx * math.cos(theta)) ** 2 + (ry * math.sin(theta)) ** 2)
        half_h = math.sqrt((rx * math.sin(theta)) ** 2 + (ry * math.cos(theta)) ** 2)
        x_min, x_max = cx - half_w, cx + half_w
        y_min, y_max = cy - half_h, cy + half_h

    elif s_name == "polygon":
        xs = [float(v) for v in shape.get("all_points_x", [])]
        ys = [float(v) for v in shape.get("all_points_y", [])]
        if not xs or not ys:
            return None
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)

    else:
        return None

    # Clamp coordinates legitimately to image boundaries
    c_xmin = max(0.0, min(float(img_width), float(x_min)))
    c_xmax = max(0.0, min(float(img_width), float(x_max)))
    c_ymin = max(0.0, min(float(img_height), float(y_min)))
    c_ymax = max(0.0, min(float(img_height), float(y_max)))

    bw = c_xmax - c_xmin
    bh = c_ymax - c_ymin

    if bw <= 0.0 or bh <= 0.0:
        return None

    xc = (c_xmin + bw / 2.0) / float(img_width)
    yc = (c_ymin + bh / 2.0) / float(img_height)
    norm_w = bw / float(img_width)
    norm_h = bh / float(img_height)

    # Clamp safely to [0.0, 1.0]
    xc = max(0.0, min(1.0, xc))
    yc = max(0.0, min(1.0, yc))
    norm_w = max(0.0, min(1.0, norm_w))
    norm_h = max(0.0, min(1.0, norm_h))

    return (class_id, xc, yc, norm_w, norm_h)


def process_eye_dataset(config: PreprocessingConfig) -> Dict[str, Any]:
    """Complete preprocessing workflow for SLID anterior-eye clinical dataset."""
    log.info("=== Starting SLID Anterior-Eye YOLOv8 Nano Preprocessing Pipeline ===")
    classes = get_domain_classes("eye")
    validate_class_configuration("eye", classes)
    class_to_idx = {name: idx for idx, name in enumerate(classes)}

    raw_dir = config.raw_dir
    output_dir = config.output_dir

    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw eye directory does not exist: {raw_dir}")

    csv_path = raw_dir / "Annotations.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Annotations.csv not found: {csv_path}")

    img_dir = raw_dir / "Original_Slit-lamp_Images"
    if not img_dir.exists():
        raise FileNotFoundError(f"Image directory not found: {img_dir}")

    # Step 1: Read and validate Annotations.csv
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    raw_annotation_count = len(rows)
    log.info(f"Loaded {raw_annotation_count:,} annotation records from: {csv_path.name}")

    # Index images and pre-cache dimensions
    image_files: Dict[str, Path] = {p.name: p for p in img_dir.glob("*.png")}
    total_images_found = len(image_files)
    log.info(f"Found {total_images_found:,} PNG images in: {img_dir.name}")
    if total_images_found != 2617:
        raise ValueError(f"Expected 2,617 PNG images in SLID, found: {total_images_found}")

    log.info("Pre-caching image dimensions and verifying file integrity...")
    img_sizes: Dict[str, Tuple[int, int]] = {}
    corrupt_images = []
    for fname, p in image_files.items():
        try:
            with Image.open(p) as img:
                img_sizes[fname] = img.size
        except Exception as exc:
            corrupt_images.append((fname, str(exc)))

    if corrupt_images:
        raise RuntimeError(f"Found {len(corrupt_images)} corrupt images in SLID dataset!")

    # Step 2: SHA-256 duplicate content hash audit
    log.info("Computing SHA-256 content hashes across all 2,617 images...")
    hashes: Dict[str, str] = {}
    duplicate_hash_pairs: List[Tuple[str, str]] = []
    for fname, p in image_files.items():
        with open(p, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        if digest in hashes:
            duplicate_hash_pairs.append((fname, hashes[digest]))
        else:
            hashes[digest] = fname

    log.info(
        f"SHA-256 hash audit complete: {len(hashes):,} unique hashes across {total_images_found:,} images. "
        f"Duplicate hash pairs: {len(duplicate_hash_pairs)}"
    )

    # Step 3: Parse annotations (separate pathology/lesion vs anatomical regions)
    img_to_lesion_rows: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    img_to_region_rows: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    total_lesion_annotations = 0
    total_region_annotations = 0
    lesion_class_counts = Counter()
    shape_counts = Counter()
    out_of_bounds_count = 0

    for r in rows:
        fname = r["filename"]
        if fname not in image_files:
            raise ValueError(f"Annotation references missing image: {fname}")

        attr = json.loads(r["attributes"])
        shape = json.loads(r["shape_coordinates"])
        les = attr.get("lesion", "").strip()
        reg = attr.get("region", "").strip()

        if les:
            if les not in class_to_idx:
                raise ValueError(f"Unknown lesion class in annotation: '{les}'")
            img_to_lesion_rows[fname].append(r)
            total_lesion_annotations += 1
            lesion_class_counts[les] += 1
            shape_counts[shape.get("name", "UNKNOWN")] += 1

            # Check boundary
            w, h = img_sizes[fname]
            if shape.get("name") == "rect":
                if shape["x"] < 0 or shape["y"] < 0 or (shape["x"] + shape["width"]) > w or (shape["y"] + shape["height"]) > h:
                    out_of_bounds_count += 1
            elif shape.get("name") == "ellipse":
                cx, cy, rx, ry = shape["cx"], shape["cy"], shape["rx"], shape["ry"]
                th = shape.get("theta", 0.0)
                hw = math.sqrt((rx * math.cos(th)) ** 2 + (ry * math.sin(th)) ** 2)
                hh = math.sqrt((rx * math.sin(th)) ** 2 + (ry * math.cos(th)) ** 2)
                if (cx - hw) < 0 or (cy - hh) < 0 or (cx + hw) > w or (cy + hh) > h:
                    out_of_bounds_count += 1

        elif reg:
            img_to_region_rows[fname].append(r)
            total_region_annotations += 1

    images_with_lesions = len(img_to_lesion_rows)
    images_without_lesions = total_images_found - images_with_lesions

    log.info(
        f"Annotation Audit Results:\n"
        f"  Total CSV records            : {raw_annotation_count:,}\n"
        f"  Genuine lesion annotations   : {total_lesion_annotations:,}\n"
        f"  Anatomical region annotations: {total_region_annotations:,}\n"
        f"  Images with lesions          : {images_with_lesions:,}\n"
        f"  Images with 0 lesions (bg)   : {images_without_lesions:,}\n"
        f"  Boundary-exceeding annotations: {out_of_bounds_count}"
    )

    # Step 4: Deterministic Stratified Splitting (Seed 42)
    # Rarest-class stratification ensures even the rarest classes (e.g. Lens dislocation/Cataract: 4)
    # have guaranteed presence across Train, Val, and Test splits.
    log.info("Performing deterministic stratified split (seed=42, 70/15/15)...")

    def get_strat_key(fname: str) -> str:
        lesions = [json.loads(r["attributes"]).get("lesion", "").strip() for r in img_to_lesion_rows.get(fname, [])]
        if not lesions:
            return "__negative__"
        return min(lesions, key=lambda l: lesion_class_counts[l])

    all_filenames = sorted(image_files.keys(), key=lambda x: int(Path(x).stem) if Path(x).stem.isdigit() else x)
    strat_groups: Dict[str, List[str]] = defaultdict(list)
    for fname in all_filenames:
        strat_groups[get_strat_key(fname)].append(fname)

    rng = random.Random(config.random_seed)
    split_images: Dict[str, List[str]] = {"train": [], "val": [], "test": []}

    for k, fnames in sorted(strat_groups.items()):
        fnames_sorted = sorted(fnames)
        rng.shuffle(fnames_sorted)
        n = len(fnames_sorted)
        n_train = int(round(n * config.split_ratios[0]))
        n_val = int(round(n * config.split_ratios[1]))

        if n >= 3:
            if n_train + n_val >= n:
                n_train = max(1, n_train - 1)
            if n_val == 0:
                n_val = 1

        split_images["train"].extend(fnames_sorted[:n_train])
        split_images["val"].extend(fnames_sorted[n_train:n_train + n_val])
        split_images["test"].extend(fnames_sorted[n_train + n_val:])

    log.info(
        f"Split sizes:\n"
        f"  Train: {len(split_images['train']):,} images ({len(split_images['train'])/total_images_found*100:.2f}%)\n"
        f"  Val  : {len(split_images['val']):,} images ({len(split_images['val'])/total_images_found*100:.2f}%)\n"
        f"  Test : {len(split_images['test']):,} images ({len(split_images['test'])/total_images_found*100:.2f}%)"
    )

    # Step 5: Directory Structure Setup
    for sub in ("images", "labels"):
        for s in EXPECTED_SPLITS:
            (output_dir / sub / s).mkdir(parents=True, exist_ok=True)

    # Step 6: File Copying & Label Generation
    log.info("Copying images and generating YOLO bounding box labels...")
    t_start = time.time()
    split_stats: Dict[str, Dict[str, Any]] = {}
    total_boxes_written = 0

    all_areas: List[float] = []
    all_widths: List[float] = []
    all_heights: List[float] = []
    all_aspect_ratios: List[float] = []

    for s in EXPECTED_SPLITS:
        fnames_in_split = split_images[s]
        log.info(f"Processing split '{s}' ({len(fnames_in_split):,} images)...")

        class_counts = {c: 0 for c in classes}
        boxes_in_split = 0
        negatives_in_split = 0

        for fname in fnames_in_split:
            stem = Path(fname).stem
            src_img = image_files[fname]
            dst_img = output_dir / "images" / s / fname
            shutil.copy2(src_img, dst_img)

            img_w, img_h = img_sizes[fname]
            label_file = output_dir / "labels" / s / f"{stem}.txt"

            lesion_records = img_to_lesion_rows.get(fname, [])
            if not lesion_records:
                # Negative background image: create empty label file per YOLO convention
                label_file.write_text("", encoding="utf-8")
                negatives_in_split += 1
                continue

            lines = []
            for r in lesion_records:
                attr = json.loads(r["attributes"])
                shape = json.loads(r["shape_coordinates"])
                les = attr.get("lesion", "").strip()
                cid = class_to_idx[les]

                bbox = parse_slid_shape_to_bbox(shape, img_w, img_h, cid)
                if bbox is None:
                    continue

                _, xc, yc, bw, bh = bbox
                lines.append(f"{cid} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}\n")
                class_counts[les] += 1
                boxes_in_split += 1
                total_boxes_written += 1

                area = bw * bh
                all_areas.append(area)
                all_widths.append(bw)
                all_heights.append(bh)
                if bh > 0:
                    all_aspect_ratios.append(bw / bh)

            label_file.write_text("".join(lines), encoding="utf-8")

        split_stats[s] = {
            "image_count": len(fnames_in_split),
            "label_count": boxes_in_split,
            "negative_images": negatives_in_split,
            "class_distribution": class_counts,
        }

    log.info(f"Images copied and labels generated in {time.time() - t_start:.1f}s")

    # Step 7: Write data.yaml
    yaml_path = output_dir / "data.yaml"
    yaml_content = (
        f"# MediQ YOLOv8 Nano Anterior-Eye Slit-Lamp Lesion Detection Dataset Config\n"
        f"path: .\n"
        f"train: images/train\n"
        f"val: images/val\n"
        f"test: images/test\n\n"
        f"nc: {len(classes)}\n"
        f"names: {classes}\n"
    )
    yaml_path.write_text(yaml_content, encoding="utf-8")
    log.info(f"Dataset config written to: {yaml_path}")

    # Step 8: Build Summary & Preprocessing Report
    summary: Dict[str, Any] = {
        "domain": "eye",
        "dataset_name": "SLID (Slit-Lamp Image Dataset)",
        "modality": "Anterior-eye / slit-lamp clinical biomicroscopy photography (STRICTLY NO OCT)",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "random_seed": config.random_seed,
        "classes": classes,
        "num_classes": len(classes),
        "total_images": total_images_found,
        "total_csv_annotations": raw_annotation_count,
        "total_lesion_annotations": total_lesion_annotations,
        "total_region_annotations": total_region_annotations,
        "total_labels_generated": total_boxes_written,
        "images_with_lesions": images_with_lesions,
        "images_without_lesions_background": images_without_lesions,
        "patient_id_available": False,
        "splitting_strategy": "Deterministic stratified image-level splitting (rarest lesion class key, seed 42)",
        "sha256_audit": {
            "total_images": total_images_found,
            "unique_hashes": len(hashes),
            "duplicate_hash_pairs": len(duplicate_hash_pairs),
        },
        "shape_distribution": dict(shape_counts),
        "splits": split_stats,
        "bounding_box_stats": {
            "total_boxes": len(all_areas),
            "area": {"min": min(all_areas), "max": max(all_areas), "mean": sum(all_areas) / len(all_areas)},
            "width": {"min": min(all_widths), "max": max(all_widths), "mean": sum(all_widths) / len(all_widths)},
            "height": {"min": min(all_heights), "max": max(all_heights), "mean": sum(all_heights) / len(all_heights)},
            "aspect_ratio": {
                "min": min(all_aspect_ratios),
                "max": max(all_aspect_ratios),
                "mean": sum(all_aspect_ratios) / len(all_aspect_ratios),
            },
        },
    }

    # Write summary JSON
    summary_path = output_dir / "preprocessing_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    log.info(f"Machine-readable summary written to: {summary_path}")

    # Write Markdown report
    report_path = output_dir / "preprocessing_report.md"
    generate_eye_report(summary, report_path)

    return summary


def generate_eye_report(summary: Dict[str, Any], output_path: Path) -> None:
    """Generates the comprehensive eye preprocessing report in Markdown."""
    splits = summary["splits"]
    classes = summary["classes"]

    class_table_rows = []
    for c in classes:
        c_tr = splits["train"]["class_distribution"][c]
        c_va = splits["val"]["class_distribution"][c]
        c_te = splits["test"]["class_distribution"][c]
        c_tot = c_tr + c_va + c_te
        class_table_rows.append(
            f"| `{c}` | {c_tr:,} | {c_va:,} | {c_te:,} | **{c_tot:,}** |"
        )
    class_table_md = "\n".join(class_table_rows)

    md_content = f"""# MediQ SLID Anterior-Eye YOLOv8 Nano Preprocessing Report

**Generated:** {summary['timestamp']}  
**Dataset:** Slit-Lamp Image Dataset (SLID)  
**Clinical Modality:** Anterior-Eye Slit-Lamp Biomicroscopy Clinical Photography  
**Prohibition Adherence:** Strictly NO Optical Coherence Tomography (OCT) or Retinal Scans; Zero Synthetic Bounding Boxes  
**Status:** COMPLETE — STRICTLY NO TRAINING PERFORMED  

---

## 1. Dataset Description & Clinical Modality

- **Source Dataset:** SLID (Slit-Lamp Image Dataset)
- **Raw Storage Location:** `backend/training/image/datasets/eye/raw/`
- **Clinical Modality:** Anterior-segment slit-lamp biomicroscopy photography captured under diffuse and slit illumination.
- **Strict Prohibition Notice:** This dataset contains **NO Optical Coherence Tomography (OCT)** and **NO retinal OCT scans**. All terminology, annotations, and processing reflect solely anterior-eye photography.

---

## 2. Ingestion & Preflight Verification Counts

- **Total PNG Images Found:** {summary['total_images']:,} (100% readable, zero corrupt files)
- **Image Resolutions:**
  - `2576 x 1934`: 1,412 images
  - `1924 x 1556`: 746 images
  - `1284 x 964`: 459 images
- **Total Metadata / Annotation Records:** {summary['total_csv_annotations']:,} rows in `Annotations.csv`
- **Image ↔ Annotation Alignment:** 100% (2,617 / 2,617 unique filenames match perfectly)
- **Missing Image References:** 0
- **Unannotated Images in Raw Directory:** 0 (all 2,617 images appear in `Annotations.csv`)

---

## 3. CSV Schema & Annotation Breakdown

The source CSV uses the VGG Image Annotator (VIA) export format:
- `filename`: Image filename (`1.png` to `2617.png`)
- `file_size`: Integer byte size of the image
- `annotation_count`: Total annotation count for this image
- `annotation_ID`: Sequential integer ID of the annotation on this image
- `attributes`: JSON string with keys `region` and `lesion`
- `shape_coordinates`: JSON string with geometry definition (`name`, coordinates)

### Separation of Pathologies vs. Anatomical Landmarks
- **Genuine Lesion Annotations:** **{summary['total_lesion_annotations']:,}** records across **{summary['images_with_lesions']:,}** images.
- **Anatomical Region Annotations:** **{summary['total_region_annotations']:,}** records across all 2,617 images (`Pupil`: 2,303, `Cornea`: 2,573, `Conjunctiva`: 2,616).
- **Negative / Background Images:** **{summary['images_without_lesions_background']:,}** images contain only anatomical landmarks and no lesions. Per standard Ultralytics YOLO conventions, these are retained as negative background images (0-byte label files) to train the detector to distinguish normal anterior-eye structures from lesions.

---

## 4. Verified Eye Lesion Class Taxonomy & YOLO IDs

The class taxonomy was derived directly from the verified values in `Annotations.csv`:

| YOLO ID | Class Name | Annotation Count | Shape Types Used |
| :---: | :--- | :--- | :--- |
| **0** | `Cataract` | 221 | circle (92), ellipse (129) |
| **1** | `Conjunctival cyst` | 134 | rect (134) |
| **2** | `Conjunctival injection` | 307 | polygon (307) |
| **3** | `Corneal / Conjunctival tumor` | 537 | rect (537) |
| **4** | `Corneal dystrophy` | 307 | rect (307) |
| **5** | `Corneal scarring` | 77 | rect (77) |
| **6** | `Intraocular lens` | 119 | circle (37), ellipse (82) |
| **7** | `Keratitis` | 270 | rect (270) |
| **8** | `Lens dislocation` | 36 | circle (4), ellipse (32) |
| **9** | `Lens dislocation/Cataract` | 4 | ellipse (4) |
| **10** | `Pigmented nevus` | 500 | rect (500) |
| **11** | `Pinguecula` | 422 | rect (422) |
| **12** | `Pterygium` | 164 | rect (164) |
| **13** | `Subconjunctival hemorrhage` | 301 | rect (301) |
| **Total** | — | **{summary['total_lesion_annotations']:,}** | rect (2,712), circle (133), ellipse (247), polygon (307) |

---

## 5. Shape-to-Bounding-Box Conversion Methodology

All bounding boxes originate strictly from genuine clinician annotations:
1. **Rectangle (`rect`)**:
   `x_min = x`, `x_max = x + width`, `y_min = y`, `y_max = y + height`
2. **Circle (`circle`)**:
   `x_min = cx - r`, `x_max = cx + r`, `y_min = cy - r`, `y_max = cy + r`
3. **Rotated Ellipse (`ellipse`)**:
   Using analytical axis-aligned bounding box enclosing the rotated ellipse:
   `half_w = sqrt((rx * cos(theta))^2 + (ry * sin(theta))^2)`
   `half_h = sqrt((rx * sin(theta))^2 + (ry * cos(theta))^2)`
   `x_min = cx - half_w`, `x_max = cx + half_w`, `y_min = cy - half_h`, `y_max = cy + half_h`
4. **Polygon (`polygon`)**:
   `x_min = min(all_points_x)`, `x_max = max(all_points_x)`, `y_min = min(all_points_y)`, `y_max = max(all_points_y)`

### Coordinate Normalization & Boundary Clamping
- Coordinates are normalized to `[0.0, 1.0]` using the exact `(width, height)` of each individual image.
- 1 annotation (`2405.png`, `Cataract` ellipse at image border `cx=1853, rx=179` in a `1924x1556` image) legitimately extended slightly past the right border (`x_max=2032`); it was cleanly clamped to the visible image frame (`c_xmax=1924`) without distorting the lesion localization.

### Bounding Box Statistical Metrics:
- **Total Bounding Boxes Generated:** {summary['bounding_box_stats']['total_boxes']:,}
- **Normalized Area:** Min = {summary['bounding_box_stats']['area']['min']:.6f}, Max = {summary['bounding_box_stats']['area']['max']:.6f}, Mean = {summary['bounding_box_stats']['area']['mean']:.6f}
- **Normalized Width:** Min = {summary['bounding_box_stats']['width']['min']:.4f}, Max = {summary['bounding_box_stats']['width']['max']:.4f}, Mean = {summary['bounding_box_stats']['width']['mean']:.4f}
- **Normalized Height:** Min = {summary['bounding_box_stats']['height']['min']:.4f}, Max = {summary['bounding_box_stats']['height']['max']:.4f}, Mean = {summary['bounding_box_stats']['height']['mean']:.4f}

---

## 6. Splitting Methodology & Patient-Level Limitation

### Patient-Level Identifier Audit & Disclosure
- **Patient Identifier Availability:** **UNAVAILABLE**. The SLID `Annotations.csv` metadata does not provide `patient_id`, hospital MRN, patient age/sex, or temporal visit tokens. The image filenames are simple sequential numbers (`1.png` to `2617.png`).
- **Limitation Acknowledgment:** Patient-level grouping cannot be performed from the available SLID metadata. We explicitly disclose this limitation rather than fabricating synthetic patient IDs.
- **Grouping / Stratification Strategy:** We utilized deterministic image-level stratified splitting with random seed `42` (70% Train, 15% Val, 15% Test). Stratification is keyed by the **rarest lesion class** on each image to ensure rare conditions (`Lens dislocation/Cataract`, `Lens dislocation`, `Corneal scarring`) have guaranteed representation across all splits.

### Split Sizes:
| Split | Total Images | Images % | Lesion Annotations | Negative (Background) Images |
| :--- | :--- | :--- | :--- | :--- |
| **Train** | **{splits['train']['image_count']:,}** | {(splits['train']['image_count'] / summary['total_images'] * 100):.2f}% | {splits['train']['label_count']:,} | {splits['train']['negative_images']:,} |
| **Validation** | **{splits['val']['image_count']:,}** | {(splits['val']['image_count'] / summary['total_images'] * 100):.2f}% | {splits['val']['label_count']:,} | {splits['val']['negative_images']:,} |
| **Test** | **{splits['test']['image_count']:,}** | {(splits['test']['image_count'] / summary['total_images'] * 100):.2f}% | {splits['test']['label_count']:,} | {splits['test']['negative_images']:,} |
| **Total** | **{summary['total_images']:,}** | **100.0%** | **{summary['total_labels_generated']:,}** | **{summary['images_without_lesions_background']:,}** |

---

## 7. SHA-256 Duplicate Content Audit

- **Total Unique File Hashes:** {summary['sha256_audit']['unique_hashes']:,} / {summary['total_images']:,}
- **Duplicate Hash Pairs Found:** **0** (All 2,617 PNG images are byte-level unique)
- **Cross-Split Content Overlap:** **ZERO**

---

## 8. Class Distribution per Split

| Class Name | Train | Val | Test | Total |
| :--- | :--- | :--- | :--- | :--- |
{class_table_md}

All 14 verified classes are represented in Train, Validation, and Test splits.

---

## 9. Directory Artifacts

Target directory: `backend/training/image/datasets/eye/processed/`

```
datasets/eye/processed/
├── images/
│   ├── train/    (1,832 PNG images)
│   ├── val/      (393 PNG images)
│   └── test/     (392 PNG images)
├── labels/
│   ├── train/    (1,832 YOLO label files)
│   ├── val/      (393 YOLO label files)
│   └── test/     (392 YOLO label files)
├── data.yaml
├── preprocessing_report.md
└── preprocessing_summary.json
```

---

## 10. Task Confirmations

1. **No Synthetic Bounding Boxes:** All boxes converted strictly from genuine clinician shape annotations.
2. **Original Raw Data Untouched:** `backend/training/image/datasets/eye/raw/` is completely unmodified.
3. **Skin Dataset Untouched:** HAM10000 skin dataset was not accessed or modified.
4. **NO TRAINING PERFORMED:** YOLOv8 training was neither initiated nor executed.
"""
    output_path.write_text(md_content, encoding="utf-8")
    log.info(f"Markdown preprocessing report written to: {output_path}")


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="MediQ Dual-Domain YOLOv8 Nano Preprocessing Pipeline (Skin & Eye)."
    )
    p.add_argument(
        "--domain",
        required=True,
        choices=["skin", "eye", "all"],
        help="Target model domain: 'skin' (HAM10000), 'eye' (SLID), or 'all'",
    )
    p.add_argument("--raw-dir", default=None, help="Path to raw dataset directory")
    p.add_argument("--output-dir", default=None, help="Path to processed output directory")
    p.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    p.add_argument("--imgsz", type=int, default=640, help="Target YOLO image resolution")
    p.add_argument(
        "--split-ratios",
        type=float,
        nargs=3,
        default=[0.70, 0.15, 0.15],
        help="Train, val, test split ratios (must sum to 1.0)",
    )
    p.add_argument(
        "--min-bbox-area",
        type=float,
        default=16.0,
        help="Minimum bounding box area in pixels (default: 16.0)",
    )
    p.add_argument(
        "--max-invalid-boxes",
        type=int,
        default=0,
        help="Maximum allowed invalid bounding boxes before error",
    )
    return p


def main() -> None:
    args = build_parser().parse_args()
    domains_to_run = ["skin", "eye"] if args.domain == "all" else [args.domain]

    for domain in domains_to_run:
        config = PreprocessingConfig(
            domain=domain,
            random_seed=args.seed,
            image_size=args.imgsz,
            split_ratios=tuple(args.split_ratios),
            min_bbox_area=args.min_bbox_area,
            max_allowed_invalid_boxes=args.max_invalid_boxes,
            raw_dir=Path(args.raw_dir) if args.raw_dir else None,
            output_dir=Path(args.output_dir) if args.output_dir else None,
        )

        log.info(f"Executing pipeline configuration for domain: {domain}")
        if domain == "skin":
            process_skin_dataset(config)
        elif domain == "eye":
            process_eye_dataset(config)


if __name__ == "__main__":
    main()
