# MediQ Dual-Domain YOLOv8 Nano Medical Image Training Pipeline

## 1. Overview & Safety Notice

This pipeline establishes the training, checkpointing, evaluation, and export workflow for MediQ's two specialized medical image analysis models:
1. **Skin Image Model**: HAM10000 dermoscopy dataset with lesion segmentation masks converted deterministically into YOLO bounding boxes across 7 diagnostic classes.
2. **Eye Image Model**: Slit-Lamp Image Dataset (SLID) anterior-eye clinical photography with genuine expert multi-shape annotations across 14 verified lesion classes.

> [!IMPORTANT]
> **PIPELINE PREPARATION ONLY — ZERO LOCAL TRAINING**  
> No model training was executed during this preparation phase. No GPU compute was consumed. No pretrained model weights (`yolov8n.pt`) were downloaded. Raw and processed datasets remain strictly untouched. Training will be conducted in **Google Colab** with GPU acceleration and persistent Google Drive storage.

---

## 2. Dataset Architecture & Clinical Modalities

| Domain | Model Backbone | Clinical Modality | Source Dataset | Split Scheme | Classes | Total Images |
|---|---|---|---|---|---|---|
| **Skin** | YOLOv8 Nano (`yolov8n.pt`) | Dermoscopy | HAM10000 (ISIC 2018 Task 3) | Lesion-grouped stratified split (`lesion_id`) | 7 diagnostic categories | 10,015 |
| **Eye** | YOLOv8 Nano (`yolov8n.pt`) | Anterior-Eye Slit-Lamp Clinical Photography | SLID | Class-stratified image split | 14 verified lesion categories | 2,617 |

### Critical Modality Constraints & Limitations
* **SLID Anterior-Eye / Slit-Lamp Photography**: The eye model strictly utilizes anterior-segment slit-lamp clinical photographs. Retinal OCT / OCT scans are **strictly prohibited** from this pipeline.
* **SLID Patient-Level Limitation**: In the SLID dataset, patient IDs are not provided in `Annotations.csv` (only image filenames and lesion annotations). Splitting was performed using stratified image-level sampling to preserve class distributions. While visual deduplication was verified, absolute patient-level isolation cannot be guaranteed due to upstream metadata absence.
* **HAM10000 Lesion-Level Grouping**: HAM10000 provides `lesion_id` metadata. Preprocessing used lesion-grouped stratified splitting to ensure zero cross-split leakage (all images from the same lesion belong strictly to a single split).
* **Genuine Annotations Only**: No synthetic bounding boxes were generated. All labels derive from expert masks (HAM10000) or clinician coordinates (SLID).

---

## 3. Verified Diagnostic Class Taxonomies

### Skin Diagnostic Classes (7 HAM10000 Classes)
```yaml
names:
  0: akiec  # Actinic keratoses and intraepithelial carcinoma / Bowen's disease
  1: bcc    # Basal cell carcinoma
  2: bkl    # Benign keratosis-like lesions (solar lentigines / seborrheic / lichenoid keratoses)
  3: df     # Dermatofibroma
  4: mel    # Melanoma
  5: nv     # Melanocytic nevi
  6: vasc   # Vascular lesions (angiomas, pyogenic granulomas, hemorrhage)
```

### Eye Pathology Classes (14 SLID Lesion Classes)
```yaml
names:
  0: Cataract
  1: Conjunctival cyst
  2: Conjunctival injection
  3: Corneal / Conjunctival tumor
  4: Corneal dystrophy
  5: Corneal scarring
  6: Intraocular lens
  7: Keratitis
  8: Lens dislocation
  9: Lens dislocation/Cataract
  10: Pigmented nevus
  11: Pinguecula
  12: Pterygium
  13: Subconjunctival hemorrhage
```
*Note: Anatomical landmarks (e.g. Cornea, Conjunctiva, Pupil) are excluded from the lesion detector.*

---

## 4. Directory Structure

```
backend/training/image/
├── datasets/
│   ├── skin/
│   │   ├── raw/                      # Original HAM10000 images, masks, and metadata
│   │   └── processed/
│   │       ├── images/ {train, val, test}
│   │       ├── labels/ {train, val, test}
│   │       ├── data.yaml             # 7-class configuration
│   │       ├── preprocessing_report.md
│   │       └── preprocessing_summary.json
│   └── eye/
│       ├── raw/                      # Annotations.csv and 2,617 slit-lamp PNGs
│       └── processed/
│           ├── images/ {train, val, test}
│           ├── labels/ {train, val, test}
│           ├── data.yaml             # 14-class configuration
│           ├── preprocessing_report.md
│           └── preprocessing_summary.json
├── runs/                             # Isolated local training runs (ignored by git)
│   ├── mediq_skin/
│   └── mediq_eye/
├── preprocess.py                     # Dataset preprocessing & verification
├── train.py                          # Dual-domain YOLOv8n trainer with Drive support
├── evaluate.py                       # Precision, Recall, mAP50, mAP50-95 evaluator
├── export.py                         # Deployment exporter & metadata generator
└── README.md                         # This pipeline documentation
```

---

## 5. Google Drive Persistence & Colab Directory Layout

Google Colab runtimes are ephemeral. To safeguard all training progress, models, and evaluation outputs, the pipeline supports writing directly to persistent Google Drive.

The persistent Drive structure is:
```
Google Drive/
└── MediQ/
    └── training/
        └── image/
            ├── skin/
            │   ├── runs/             # TensorBoard events, curves, confusion matrix
            │   ├── checkpoints/      # best_skin.pt, last_skin.pt
            │   ├── evaluation/       # eval_val_metrics.json, eval_test_metrics.json
            │   └── exports/          # latest.pt, model_metadata.json
            └── eye/
                ├── runs/             # TensorBoard events, curves, confusion matrix
                ├── checkpoints/      # best_eye.pt, last_eye.pt
                ├── evaluation/       # eval_val_metrics.json, eval_test_metrics.json
                └── exports/          # latest.pt, model_metadata.json
```

---

## 6. Pipeline CLI Command Reference

### A. Preflight Validation (Run Locally or in Colab Without Weights)
Verify dataset paths, label formats, class taxonomies, and CLI arguments without downloading weights or training:
```bash
# Training pipeline validation
python backend/training/image/train.py --domain skin --validate_only
python backend/training/image/train.py --domain eye --validate_only

# Evaluation pipeline validation
python backend/training/image/evaluate.py --domain skin --validate_only
python backend/training/image/evaluate.py --domain eye --validate_only

# Export pipeline validation
python backend/training/image/export.py --domain skin --validate_only
python backend/training/image/export.py --domain eye --validate_only
```

### B. Training in Google Colab (GPU)
Execute independent training runs for Skin and Eye models with Google Drive persistence:
```bash
# Train Skin Model (HAM10000 7-class) on Colab T4/V100 GPU:
python train.py \
    --domain skin \
    --epochs 50 \
    --batch 16 \
    --imgsz 640 \
    --save_period 5 \
    --patience 20 \
    --google_drive

# Train Eye Model (SLID 14-class) on Colab T4/V100 GPU:
python train.py \
    --domain eye \
    --epochs 50 \
    --batch 16 \
    --imgsz 640 \
    --save_period 5 \
    --patience 20 \
    --google_drive
```

### C. Resuming an Interrupted Run
If a Colab runtime disconnects or times out, resume training from the latest checkpoint:
```bash
python train.py --domain skin --resume --google_drive
python train.py --domain eye --resume --google_drive
```

### D. Model Evaluation
Evaluate the trained model on held-out validation and test sets (never training set):
```bash
# Evaluate on held-out test split:
python evaluate.py --domain skin --split test --google_drive
python evaluate.py --domain eye --split test --google_drive

# Evaluate on both validation and test splits:
python evaluate.py --domain skin --split all --google_drive
python evaluate.py --domain eye --split all --google_drive
```
Metrics produced: Precision, Recall, mAP@50, mAP@50-95, and per-class metrics saved in `eval_test_metrics.json`.

### E. Model Export
Export the best trained checkpoint to MediQ's active runtime location:
```bash
# Export models to backend/models/image/<domain>/latest.pt:
python export.py --domain skin --google_drive
python export.py --domain eye --google_drive
```
Target runtime artifacts created:
* `backend/models/image/skin/latest.pt`
* `backend/models/image/skin/model_metadata.json`
* `backend/models/image/eye/latest.pt`
* `backend/models/image/eye/model_metadata.json`

---

## 7. Future Step-by-Step Google Colab Workflow

When ready to train on a Colab GPU instance, execute the following procedure:

1. **Mount Google Drive**:
   ```python
   from google.colab import drive
   drive.mount('/content/drive')
   ```
2. **Sync Prepared Datasets**:
   Ensure preprocessed datasets are located at:
   `/content/drive/MyDrive/MediQ/datasets/skin/processed/` and
   `/content/drive/MyDrive/MediQ/datasets/eye/processed/` (or copy them from the repository).
3. **Install Dependencies**:
   ```bash
   pip install ultralytics torch torchvision pyyaml
   ```
4. **Preflight Validation**:
   ```bash
   python train.py --domain skin --validate_only
   python train.py --domain eye --validate_only
   ```
5. **Download Pretrained YOLOv8 Nano Weights**:
   The script will automatically fetch `yolov8n.pt` once actual training starts.
6. **Launch Training**:
   Run `python train.py --domain <domain> --google_drive` so outputs write directly into Drive.
7. **Verify Checkpoints**:
   Confirm `best_<domain>.pt` and `last_<domain>.pt` are saved in Drive `checkpoints/`.
8. **Evaluate Held-Out Splits**:
   Run `python evaluate.py --domain <domain> --split all --google_drive`.
9. **Export Best Model**:
   Run `python export.py --domain <domain> --google_drive`.
10. **Deploy to MediQ**:
    Copy `latest.pt` and `model_metadata.json` into `backend/models/image/<domain>/`.
