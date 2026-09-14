# MediQ — DistilBERT Stage 1 Symptom Classification Pipeline

This directory contains the production-grade training, evaluation, and export pipeline for fine-tuning `distilbert-base-uncased` on **DDXPlus** (49 pathologies).
It is specifically designed for execution in Google Colab with **mandatory Google Drive persistence** to ensure that no checkpoints, run logs, or evaluation results can be lost upon runtime disconnect.

---

## 1. Directory Structure

```
training/symptom/
├── processed/
│   ├── ddxplus/
│   │   ├── train/ddx_train.jsonl          # 1,025,602 records (49 classes)
│   │   ├── validate/ddx_validate.jsonl    # 132,448 records (49 classes)
│   │   └── test/ddx_test.jsonl            # 134,529 records (49 classes)
│   ├── symptom2disease/
│   │   ├── train/s2d_train.jsonl          # 917 records (Stage 2)
│   │   ├── validate/s2d_validate.jsonl    # 117 records (Stage 2)
│   │   └── test/s2d_test.jsonl            # 119 records (External evaluation)
│   ├── kerala/
│   │   └── evaluation/kerala_eval.jsonl   # 24 records (External evaluation)
│   ├── label_mapping/
│   │   ├── stage1_label_mapping.json      # Exact 49 DDXPlus class id2label & label2id
│   │   └── label_mapping.json             # Backward-compatible label mapping
│   ├── preprocessing_report.md
│   └── preprocessing_summary.json
├── train.py                               # Hugging Face Trainer pipeline with Google Drive persistence
├── evaluate.py                            # Official & Strict Generalization evaluation pipeline
├── export.py                              # Deployment export pipeline (models/symptom/stage1 and latest)
├── train_colab.ipynb                      # 14-step ready-to-run Google Colab GPU notebook
├── validate_architecture.py               # In-memory Stage 1 & Stage 2 architectural validation
└── README.md                              # This document
```

---

## 2. Model Architecture & Data Constraints

- **Base Model**: `distilbert-base-uncased` (6 layers, 768 hidden, 12 attention heads, 66M parameters)
- **Target Label**: DDXPlus `PATHOLOGY` (49 diagnostic categories)
- **Input Text**: Deterministic natural-language presentation generated from:
  - Patient age and sex (e.g. `Patient is a 45-year-old Male.`)
  - Initial presentation evidence translated to English question format
  - All positive clinical evidences (symptoms, antecedents, risk factors) with categorical/binary value meanings
- **Strict Leakage Prevention**:
  - `DIFFERENTIAL_DIAGNOSIS` is **NEVER** used as an input feature
  - `PATHOLOGY` is **NEVER** used as an input feature
  - Input features contain only presentation/evidence data
- **Stage 1 Data Scope**:
  - Only DDXPlus data (`ddx_train.jsonl` and `ddx_validate.jsonl`) is used for model training
  - `Symptom2Disease` and `Kerala` data are **NOT** used in Stage 1 training

---

## 3. Persistent Google Drive Storage

All future training, evaluation, and export operations in Google Colab write directly to Google Drive:

```
Google Drive/
└── MediQ/
    └── training/
        └── symptom/
            ├── stage1/
            │   ├── runs/          # Training run artifacts and logs
            │   ├── checkpoints/   # Model checkpoints (e.g. checkpoints/best)
            │   ├── evaluation/    # Evaluation metrics JSON files
            │   └── exports/       # Deployment-ready model packages
            └── stage2/            # Reserved for future Stage 2 fine-tuning
```

### Google Drive Pre-Training Guard
Before any training or checkpoint creation begins, `train.py` verifies:
1. `/content/drive` exists.
2. `/content/drive/MyDrive` exists.
3. The configured directory hierarchy exists or can be created.
4. Performs an actual file write and deletion test.
5. If Drive is missing or unwritable, execution halts **immediately** with an informative error.
6. Models are **never** trained in temporary `/content` to be copied afterward.

---

## 4. Preflight Validation

Before running GPU training in Colab, run preflight validation:

### Local Preflight (No GPU, No Weights Saved)
```bash
python train.py --validate_only
```
Preflight validates:
- Processed DDXPlus dataset files exist and are readable.
- All 49 labels match `stage1_label_mapping.json`.
- Forbidden fields (`DIFFERENTIAL_DIAGNOSIS`, `PATHOLOGY`) are absent from input text.
- Tokenizer loads and tokenizes sample input.
- Pretrained DistilBERT architecture loads with 49-class head.
- In-memory forward pass succeeds with shape `[1, 49]`.
- No model weights are saved to disk.

### Drive Guard Verification
```bash
python train.py --validate_only --google_drive
```
On Windows/local environments without Google Drive mounted at `/content/drive`, this command safely terminates with exit code 1, confirming the protection guard is active.

---

## 5. Evaluation Splits & Methodology

`evaluate.py` evaluates the fine-tuned checkpoint across 4 distinct evaluation regimes:

### 1. Official DDXPlus Test Split
- Benchmark: 134,529 untouched test cases.
- Metrics: Accuracy, Macro Precision, Macro Recall, Macro F1, Weighted F1, Per-Class reports, Confusion Matrix.
- Output: `Google Drive/.../stage1/evaluation/official_test_metrics.json`

### 2. Strict Generalization Evaluation
- Methodology: Filters out train↔test exact symptom presentation overlaps in-memory.
- Fingerprint definition: `SHA256(age | sex | initial_evidence | sorted_positive_evidences)`.
- Count calculation: Dynamically computed from dataset records (not hardcoded).
- Note: The source `ddx_test.jsonl` is **never** modified.
- Output: `Google Drive/.../stage1/evaluation/strict_test_metrics.json`

### 3. External Symptom2Disease Evaluation
- Evaluates the 119-record held-out test split of Symptom2Disease against the Stage 1 model.
- Cleanly differentiates:
  - In-label-space classes: `Pneumonia` and `GERD` (calculates genuine accuracy/F1).
  - Out-of-label-space classes: 22 classes (reports frequency and Stage 1 prediction distribution).
- Output: `Google Drive/.../stage1/evaluation/symptom2disease_metrics.json`

### 4. External Kerala Clinical Profile Evaluation
- Evaluates the 24-record Kerala endemic disease evaluation dataset (Nipah, Chikungunya, Leptospirosis).
- All 3 classes are out-of-label-space for Stage 1. Cleanly reports prediction distribution without crashing or silent mapping.
- Output: `Google Drive/.../stage1/evaluation/kerala_metrics.json`

---

## 6. Model Export Pipeline

`export.py` packages the trained checkpoint for deployment into the MediQ FastAPI backend:

```bash
# Export trained checkpoint from Google Drive
python export.py --google_drive
```

- Target directories:
  - `backend/models/symptom/stage1/`
  - `backend/models/symptom/latest/`
- Exported files:
  - `config.json`
  - `model.safetensors` or `pytorch_model.bin`
  - `tokenizer.json`, `vocab.txt`, `tokenizer_config.json`, `special_tokens_map.json`
  - `label_mapping.json` (explicit `id2label` and `label2id` mappings)
  - `model_metadata.json` (provenance, architecture, seed, Stage 2 expansion compatibility, and clinical disclaimer)

> [!CAUTION]
> If no trained checkpoint exists, `export.py` exits cleanly with code 1. It **never** creates dummy or placeholder weights.

---

## 7. Future Stage 2 Architecture Compatibility

Stage 1 is strictly architected for future Stage 2 expansion:
- **Unified Label Space**: 71 classes (49 DDXPlus + 22 S2D-only additions).
- **Weight Transfer Protocol**:
  - The 49 trained Stage 1 classifier weights and biases are copied directly into their corresponding positions in the 71-class classifier.
  - The 22 newly introduced S2D-only positions are initialized using Kaiming uniform.
- **Stage 2 Fine-Tuning**:
  - Trained on S2D training data with balanced DDXPlus experience replay (20 examples/class = 980 DDXPlus samples, seed 42) to prevent catastrophic forgetting.
  - Validated by `validate_architecture.py`.

---

## 8. Colab Execution Quick Start

1. Open Google Colab and set runtime to **T4 GPU**.
2. Mount Google Drive.
3. Open `train_colab.ipynb`.
4. Run cells 1 through 8 to verify environment, Drive persistence, and preflight checks.
5. Uncomment and execute Cell 9 to launch GPU training:
   ```bash
   python train.py \
       --google_drive \
       --drive_root /content/drive/MyDrive/MediQ/training/symptom/stage1 \
       --data_dir /content/drive/MyDrive/MediQ/processed \
       --epochs 3 \
       --batch_size 32 \
       --learning_rate 2e-5 \
       --max_seq_length 128 \
       --seed 42
   ```
6. Run Cells 10–13 to execute the 4-tier evaluation suite.
7. Run Cell 14 to export the final model to persistent storage.
