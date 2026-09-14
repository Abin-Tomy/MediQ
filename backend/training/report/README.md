# MediQ T5-Small Medical & Scientific Report Summarization Pipeline

## 1. Overview & Important Clinical Limitations

This pipeline prepares, fine-tunes, evaluates, and exports a **T5-small** model for abstractive text summarization.

> [!IMPORTANT]
> **DATASET PURPOSE & NON-CLINICAL NATURE**:
> - The training dataset is the PubMed configuration of `armanc/scientific_papers`.
> - It contains scientific biomedical research paper bodies (`article`) paired with their author abstracts (`abstract`).
> - It serves strictly as a **domain-related technical proxy** for long-context biomedical text summarization.
> - **It is NOT a clinical patient-report dataset.**
> - **It does NOT contain electronic health records (EHRs), patient clinical notes, or pathology laboratory reports.**
> - **It is NOT clinically validated for medical diagnosis, treatment planning, or clinical decision support.**
> - Summaries produced by this model must be treated as informational aids and must never replace clinical judgment.

> [!NOTE]
> **STAGE 3 PIPELINE PREPARATION — NO LOCAL TRAINING**:
> No training was executed locally during this pipeline preparation phase. No GPU compute was consumed. Preprocessing and preflight validation routines verify data and model loading without generating weights. Training is configured to run on **Google Colab GPU** with direct, persistent **Google Drive storage**.

---

## 2. Model Architecture & Configuration

| Parameter | Specification |
|---|---|
| **Base Model** | `t5-small` (60.5M parameters, encoder-decoder transformer) |
| **Task Formulation** | Abstractive text-to-text sequence generation |
| **Task Prefix** | `"summarize: "` (standard T5 conditional generation prefix) |
| **Max Source Tokens** | `512` (configurable via `--max_source_length`) |
| **Max Target Tokens** | `128` (configurable via `--max_target_length`) |
| **Tokenizer** | `AutoTokenizer.from_pretrained("t5-small")` (SentencePiece-backed) |
| **Data Collator** | `DataCollatorForSeq2Seq` (dynamic padding, `label_pad_token_id=-100`) |
| **Precision** | FP16 mixed precision on CUDA GPU; automatic float32 fallback on CPU |

---

## 3. Dataset Preprocessing Summary

The raw PubMed dataset (`armanc/scientific_papers`) was processed deterministically into clean, leakage-safe JSONL splits stored at `backend/training/report/processed/`:

| Split | Raw Records | Filtered Empty Articles | Clean Records | Total File Size | Avg Article Length | Avg Abstract Length |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Train** | 119,924 | 2,816 | **117,108** | 2,135.28 MB | 3,116 words | 203 words |
| **Validation** | 6,633 | 2 | **6,631** | 120.93 MB | 3,112 words | 203 words |
| **Test** | 6,658 | 0 | **6,658** | 120.79 MB | 3,092 words | 205 words |
| **Total** | **133,215** | **2,818** | **130,397** | **2,377.00 MB** | **3,115 words** | **203 words** |

### JSONL Record Schema
Each line in `data.jsonl` contains:
```json
{
  "article": "Full scientific text of the paper...",
  "abstract": "Author abstract summarizing findings..."
}
```

---

## 4. Google Colab + Google Drive Persistence Architecture

Because Google Colab runtimes are ephemeral, **all training checkpoints, evaluation outputs, and exported artifacts are written directly to Google Drive**.

The directory structure on Google Drive is created and validated **before** training begins:
```
Google Drive/
└── MediQ/
    └── training/
        └── report/
            ├── runs/                  # TensorBoard logs and Trainer state
            ├── checkpoints/           # Periodic epoch checkpoints & best model
            ├── evaluation/            # eval_validation_metrics.json, eval_test_metrics.json
            └── exports/               # Exported model files (config, weights, metadata)
                └── t5_small_summarizer/
```

If Google Drive is not mounted or write verification fails, `train.py` aborts immediately before loading the model.

---

## 5. CLI Command Reference

All scripts are located in `backend/training/report/`:

### A. Preflight Validation Mode (Safe Non-Training Checks)
Verify dataset integrity, sample tokenization, model loading, and Drive configuration without initiating training:
```bash
# Validate training pipeline:
python train.py --validate_only

# Validate evaluation pipeline:
python evaluate.py --validate_only

# Validate test generation / inference CLI:
python infer.py --validate_only

# Validate export pipeline:
python export.py --validate_only
```

### B. Training in Google Colab (GPU)
Execute fine-tuning on a Google Colab GPU instance with Google Drive persistence:
```bash
# Recommended Colab GPU execution command:
python train.py \
    --data_dir /content/drive/MyDrive/MediQ/training/report/processed \
    --google_drive \
    --drive_root /content/drive/MyDrive/MediQ/training/report \
    --model_name t5-small \
    --epochs 3 \
    --batch_size 8 \
    --gradient_accumulation_steps 4 \
    --learning_rate 3e-4 \
    --max_source_length 512 \
    --max_target_length 128 \
    --save_period 1 \
    --fp16
```

### C. Resuming Training
If a Colab runtime is interrupted, resume directly from the latest saved checkpoint on Drive:
```bash
python train.py \
    --google_drive \
    --resume latest
```

### D. Model Evaluation (ROUGE Metrics)
Compute genuine ROUGE-1, ROUGE-2, and ROUGE-L scores on held-out validation or test splits:
```bash
# Evaluate on test split:
python evaluate.py \
    --checkpoint /content/drive/MyDrive/MediQ/training/report/exports/t5_small_summarizer \
    --split test \
    --google_drive

# Evaluate on validation split:
python evaluate.py \
    --checkpoint /content/drive/MyDrive/MediQ/training/report/exports/t5_small_summarizer \
    --split validation \
    --google_drive
```
Results are saved as structured JSON in `Google Drive/MediQ/training/report/evaluation/eval_test_metrics.json`.

### E. Test Generation / Inference
Generate an abstractive summary from raw text using a trained checkpoint:
```bash
python infer.py \
    --checkpoint /content/drive/MyDrive/MediQ/training/report/exports/t5_small_summarizer \
    --text "A 12-month study evaluated dietary interventions combined with regular exercise in adult patients..."
```

### F. Model Export for Backend Integration
Export the fine-tuned model and metadata into the MediQ FastAPI backend model directories:
```bash
python export.py --google_drive
```
This exports:
- `backend/models/report/latest/config.json`
- `backend/models/report/latest/model.safetensors`
- `backend/models/report/latest/tokenizer.json`
- `backend/models/report/latest/model_metadata.json`
*(And matching copies in `backend/models/report/` for universal runtime path resolution).*

---

## 6. Google Colab Execution Workflow

The accompanying notebook [`train_colab.ipynb`](file:///c:/Users/abint/Desktop/MediQ/backend/training/report/train_colab.ipynb) enforces the following sequential execution order:

1. **Install Dependencies**: `pip install transformers datasets evaluate rouge_score accelerate sentencepiece`
2. **Mount Google Drive**: `drive.mount('/content/drive')`
3. **Verify Drive Path & Write Access**: Write and unlink a temporary test file to ensure write permissions.
4. **Create Persistent Directories**: Initialize `runs/`, `checkpoints/`, `evaluation/`, and `exports/`.
5. **Validate Preflight**: Execute `python train.py --validate_only --google_drive` to confirm data and tokenizer readiness.
6. **Start GPU Training**: Execute `train.py` with `--fp16` and `--google_drive`.
7. **Evaluate Model**: Run `evaluate.py --split test --google_drive` to compute ROUGE benchmarks.
8. **Test Generation**: Run `infer.py` to inspect sample output.
9. **Export Artifacts**: Run `export.py` to generate backend-ready weights and metadata.

---

## 7. OCR & Report Processing Roadmap

Future report ingestion follows a modular architecture:
1. **Digital PDFs**: Text extraction via `PyMuPDF` (`fitz`).
2. **Scanned Documents**: Text extraction via `pytesseract` OCR.
3. **Summarization Service**: Extracted text passed directly to fine-tuned T5-small service via `T5ReportModel.infer(text)`.
