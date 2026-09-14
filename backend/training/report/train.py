"""
train.py — MediQ T5-Small Medical & Scientific Report Summarization Training Pipeline

Fine-tunes real pretrained T5-small on the processed PubMed scientific papers dataset
(article -> abstract) with robust Google Colab GPU support and persistent Google Drive storage.

Key Architecture:
  - Base model: t5-small (pretrained Hugging Face model)
  - Task: Abstractive text summarization
  - Task prefix: "summarize: "
  - Source data: backend/training/report/processed/{train,validation,test}/data.jsonl
  - Checkpointing: Saves periodically, tracks best model, enables resuming after interruption.
  - Google Drive Persistence: Mounts and validates Drive BEFORE trainer initializes.
  - Safe Preflight Mode: --validate_only inspects data, tokenizer, model, and Drive without training.

Important Limitations:
  - The training dataset consists of scientific biomedical literature articles and author abstracts.
  - It serves as a domain-related abstractive summarization technical proxy.
  - It is NOT a clinical patient-report dataset and is NOT clinically validated for diagnosis.
"""

import argparse
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional

import torch
from torch.utils.data import Dataset

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("train_t5_report")


# ---------------------------------------------------------------------------
# Memory-Efficient JSONL Dataset with Byte-Offset Indexing
# ---------------------------------------------------------------------------

class JSONLSummarizationDataset(Dataset):
    """
    Memory-efficient PyTorch Dataset for large JSONL summarization corpora.
    Uses byte-offset indexing to allow instant random access without loading
    the full multi-gigabyte dataset into memory.
    """

    def __init__(
        self,
        jsonl_path: Path,
        tokenizer: Any,
        prefix: str = "summarize: ",
        max_source_length: int = 512,
        max_target_length: int = 128,
        max_samples: Optional[int] = None,
    ):
        self.jsonl_path = Path(jsonl_path)
        self.tokenizer = tokenizer
        self.prefix = prefix
        self.max_source_length = max_source_length
        self.max_target_length = max_target_length

        if not self.jsonl_path.exists():
            raise FileNotFoundError(f"Processed JSONL dataset not found at: {self.jsonl_path}")

        logger.info(f"Indexing line byte-offsets for {self.jsonl_path.name}...")
        t0 = time.time()
        self.offsets: List[int] = []
        with open(self.jsonl_path, "rb") as f:
            offset = 0
            for line in f:
                self.offsets.append(offset)
                offset += len(line)
                if max_samples and len(self.offsets) >= max_samples:
                    break

        logger.info(f"Indexed {len(self.offsets):,} records in {time.time() - t0:.2f}s ({self.jsonl_path.name})")

    def __len__(self) -> int:
        return len(self.offsets)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        offset = self.offsets[idx]
        with open(self.jsonl_path, "r", encoding="utf-8") as f:
            f.seek(offset)
            line = f.readline()

        data = json.loads(line)
        source_text = self.prefix + data.get("article", "").strip()
        target_text = data.get("abstract", "").strip()

        model_inputs = self.tokenizer(
            source_text,
            max_length=self.max_source_length,
            truncation=True,
            padding=False,
        )

        labels = self.tokenizer(
            text_target=target_text,
            max_length=self.max_target_length,
            truncation=True,
            padding=False,
        )

        model_inputs["labels"] = labels["input_ids"]
        return model_inputs


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
            "Please mount Google Drive in Google Colab before training:\n"
            "    from google.colab import drive\n"
            "    drive.mount('/content/drive')"
        )
        return False

    # Verify write access
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
    Creates standard persistent directory hierarchy on Google Drive.
    """
    dirs = {
        "runs": drive_root / "runs",
        "checkpoints": drive_root / "checkpoints",
        "evaluation": drive_root / "evaluation",
        "exports": drive_root / "exports",
    }
    for name, p in dirs.items():
        p.mkdir(parents=True, exist_ok=True)
        logger.info(f"Persistent Drive directory ready [{name}]: {p}")
    return dirs


# ---------------------------------------------------------------------------
# Preflight Validation
# ---------------------------------------------------------------------------

def run_preflight_validation(
    data_dir: Path,
    model_name: str,
    prefix: str,
    max_source_length: int,
    max_target_length: int,
    google_drive: bool,
    drive_mount_path: str,
    drive_root: Path,
    output_dir: Path,
) -> bool:
    """
    Comprehensive validation check:
      - Validates processed JSONL splits exist
      - Validates schema and required non-empty fields
      - Validates tokenizer loading and sample tokenization
      - Validates model architecture loading
      - Validates Google Drive mount and write access if enabled
      - Exits cleanly without training
    """
    logger.info("=== Starting Preflight Validation: MediQ T5-Small Report Pipeline ===")

    # 1. Dataset verification
    splits = ["train", "validation", "test"]
    split_info: Dict[str, Dict[str, Any]] = {}

    for s in splits:
        p = data_dir / s / "data.jsonl"
        if not p.exists():
            logger.error(f"Dataset file missing for split '{s}': {p}")
            return False

        size_mb = p.stat().st_size / (1024 * 1024)

        # Inspect first record
        with open(p, "r", encoding="utf-8") as f:
            first_line = f.readline()
            data = json.loads(first_line)

        article = data.get("article", "")
        abstract = data.get("abstract", "")

        if not article or not isinstance(article, str):
            logger.error(f"Split '{s}' has empty or invalid 'article' in first record.")
            return False
        if not abstract or not isinstance(abstract, str):
            logger.error(f"Split '{s}' has empty or invalid 'abstract' in first record.")
            return False

        split_info[s] = {
            "path": str(p),
            "size_mb": round(size_mb, 2),
            "sample_article_chars": len(article),
            "sample_article_words": len(article.split()),
            "sample_abstract_chars": len(abstract),
            "sample_abstract_words": len(abstract.split()),
        }

    # Summary metadata file
    summary_file = data_dir / "preprocessing_summary.json"
    if summary_file.exists():
        with open(summary_file, "r", encoding="utf-8") as f:
            sum_data = json.load(f)
        logger.info(f"Verified dataset source: {sum_data.get('dataset_name')} ({sum_data.get('configuration')})")
        logger.info(
            f"Record counts: "
            f"train={sum_data.get('splits', {}).get('train', {}).get('valid_count', 117108):,}, "
            f"val={sum_data.get('splits', {}).get('validation', {}).get('valid_count', 6631):,}, "
            f"test={sum_data.get('splits', {}).get('test', {}).get('valid_count', 6658):,}"
        )

    for s, info in split_info.items():
        logger.info(f"  Split '{s:<10}': {info['size_mb']:>8.2f} MB | Sample article words: {info['sample_article_words']}, abstract words: {info['sample_abstract_words']}")

    # 2. Tokenizer & Model loading verification
    logger.info(f"Loading pretrained tokenizer: {model_name}...")
    from transformers import AutoTokenizer, T5ForConditionalGeneration

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    logger.info(f"Tokenizer loaded successfully: {type(tokenizer).__name__}")

    # Test sample tokenization
    sample_article = prefix + "A clinical study was conducted on pediatric nutritional intervention."
    sample_abstract = "Nutritional interventions significantly improved health markers."
    tok_in = tokenizer(sample_article, max_length=max_source_length, truncation=True)
    tok_out = tokenizer(text_target=sample_abstract, max_length=max_target_length, truncation=True)
    logger.info(
        f"Sample tokenization verified: "
        f"Input tokens: {len(tok_in['input_ids'])}, Target tokens: {len(tok_out['input_ids'])}"
    )

    # 3. Model Architecture Verification
    logger.info(f"Loading base model architecture: {model_name}...")
    model = T5ForConditionalGeneration.from_pretrained(model_name)
    num_params = sum(p.numel() for p in model.parameters())
    logger.info(f"Base model loaded successfully. Total parameters: {num_params:,} (~{num_params / 1e6:.1f}M)")

    # 4. Device & Precision Capabilities
    cuda_available = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if cuda_available else "CPU"
    logger.info(f"Compute environment: CUDA Available={cuda_available} | Device='{device_name}'")
    logger.info(f"FP16 capability: {'Supported (CUDA enabled)' if cuda_available else 'Disabled (CPU only)'}")

    # 5. Drive verification
    if google_drive:
        logger.info(f"Validating Google Drive mount at: {drive_mount_path}...")
        if not verify_google_drive_mount(drive_mount_path):
            return False
        dirs = setup_persistent_directories(drive_root)
        logger.info(f"Drive output target verified: {dirs['checkpoints']}")
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Local output target ready: {output_dir}")

    logger.info("PREFLIGHT VALIDATION PASSED — PIPELINE IS READY FOR GOOGLE COLAB TRAINING.")
    logger.info("NO TRAINING WAS EXECUTED (per --validate_only).")
    return True


# ---------------------------------------------------------------------------
# CLI Parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="MediQ T5-Small Report Summarization Training Pipeline (PubMed Scientific Papers Proxy)."
    )
    base_dir = Path(__file__).resolve().parent

    p.add_argument(
        "--data_dir",
        type=Path,
        default=base_dir / "processed",
        help="Path to processed dataset directory containing train/val/test data.jsonl",
    )
    p.add_argument(
        "--model_name",
        type=str,
        default="t5-small",
        help="Pretrained Hugging Face T5 model checkpoint (default: t5-small)",
    )
    p.add_argument(
        "--prefix",
        type=str,
        default="summarize: ",
        help="T5 text-to-text task prefix (default: 'summarize: ')",
    )
    p.add_argument(
        "--max_source_length",
        type=int,
        default=512,
        help="Maximum input token sequence length for articles (default: 512)",
    )
    p.add_argument(
        "--max_target_length",
        type=int,
        default=128,
        help="Maximum target token sequence length for abstracts (default: 128)",
    )
    p.add_argument(
        "--epochs",
        type=int,
        default=3,
        help="Number of training epochs (default: 3)",
    )
    p.add_argument(
        "--batch_size",
        type=int,
        default=4,
        help="Batch size per GPU/CPU device (default: 4)",
    )
    p.add_argument(
        "--gradient_accumulation_steps",
        type=int,
        default=4,
        help="Gradient accumulation steps to simulate larger batch size (default: 4)",
    )
    p.add_argument(
        "--learning_rate",
        type=float,
        default=3e-4,
        help="Initial learning rate for AdamW optimizer (default: 3e-4)",
    )
    p.add_argument(
        "--weight_decay",
        type=float,
        default=0.01,
        help="Weight decay for regularization (default: 0.01)",
    )
    p.add_argument(
        "--warmup_ratio",
        type=float,
        default=0.05,
        help="Linear warmup ratio over total training steps (default: 0.05)",
    )
    p.add_argument(
        "--save_period",
        type=int,
        default=1,
        help="Checkpoint save frequency in epochs (default: 1)",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic random seed for reproducibility (default: 42)",
    )
    p.add_argument(
        "--fp16",
        action="store_true",
        help="Enable 16-bit mixed precision on CUDA GPU",
    )
    p.add_argument(
        "--google_drive",
        action="store_true",
        help="Enforce persistent Google Drive storage for runs, checkpoints, and exports",
    )
    p.add_argument(
        "--drive_mount_path",
        type=str,
        default="/content/drive",
        help="Google Drive mount path inside Google Colab (default: /content/drive)",
    )
    p.add_argument(
        "--drive_root",
        type=Path,
        default=Path("/content/drive/MyDrive/MediQ/training/report"),
        help="Root path on Google Drive for MediQ report training artifacts",
    )
    p.add_argument(
        "--output_dir",
        type=Path,
        default=base_dir / "checkpoints",
        help="Output directory for training checkpoints (overridden by --drive_root if --google_drive is set)",
    )
    p.add_argument(
        "--export_dir",
        type=Path,
        default=base_dir / "exports" / "t5_small_summarizer",
        help="Directory where final best model is saved upon completion",
    )
    p.add_argument(
        "--resume",
        nargs="?",
        const="latest",
        default=None,
        help="Resume training from checkpoint (pass 'latest' or path to specific checkpoint folder)",
    )
    p.add_argument(
        "--max_train_samples",
        type=int,
        default=None,
        help="Optional ceiling on training records (for debugging or rapid testing)",
    )
    p.add_argument(
        "--max_val_samples",
        type=int,
        default=None,
        help="Optional ceiling on validation records",
    )
    p.add_argument(
        "--validate_only",
        action="store_true",
        help="Execute preflight dataset & environment validation without training",
    )
    return p


# ---------------------------------------------------------------------------
# Training Orchestration
# ---------------------------------------------------------------------------

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Determine persistent paths
    if args.google_drive:
        output_dir = args.drive_root / "checkpoints"
        runs_dir = args.drive_root / "runs"
        export_dir = args.drive_root / "exports" / "t5_small_summarizer"
    else:
        output_dir = args.output_dir
        runs_dir = output_dir.parent / "runs"
        export_dir = args.export_dir

    # Preflight validation mode
    if args.validate_only:
        success = run_preflight_validation(
            data_dir=args.data_dir,
            model_name=args.model_name,
            prefix=args.prefix,
            max_source_length=args.max_source_length,
            max_target_length=args.max_target_length,
            google_drive=args.google_drive,
            drive_mount_path=args.drive_mount_path,
            drive_root=args.drive_root,
            output_dir=output_dir,
        )
        if not success:
            sys.exit(1)
        return

    # Full Training Workflow (Executed in Google Colab with GPU)
    logger.info("=== Initializing Full T5-Small Report Training Run ===")

    # Enforce Google Drive persistence in production Colab runs
    if args.google_drive:
        if not verify_google_drive_mount(args.drive_mount_path):
            logger.error("Aborting training: Google Drive mount verification failed.")
            sys.exit(1)
        setup_persistent_directories(args.drive_root)

    output_dir.mkdir(parents=True, exist_ok=True)
    runs_dir.mkdir(parents=True, exist_ok=True)
    export_dir.mkdir(parents=True, exist_ok=True)

    from transformers import (
        AutoTokenizer,
        DataCollatorForSeq2Seq,
        Seq2SeqTrainer,
        Seq2SeqTrainingArguments,
        T5ForConditionalGeneration,
        set_seed,
    )

    set_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    use_fp16 = args.fp16 and (device == "cuda")

    logger.info(f"Target compute device: {device.upper()}")
    logger.info(f"Mixed precision (FP16): {use_fp16}")

    # Load Tokenizer & Model
    logger.info(f"Loading pretrained model: {args.model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    model = T5ForConditionalGeneration.from_pretrained(args.model_name)

    # Prepare Datasets
    train_file = args.data_dir / "train" / "data.jsonl"
    val_file = args.data_dir / "validation" / "data.jsonl"

    train_dataset = JSONLSummarizationDataset(
        jsonl_path=train_file,
        tokenizer=tokenizer,
        prefix=args.prefix,
        max_source_length=args.max_source_length,
        max_target_length=args.max_target_length,
        max_samples=args.max_train_samples,
    )

    val_dataset = JSONLSummarizationDataset(
        jsonl_path=val_file,
        tokenizer=tokenizer,
        prefix=args.prefix,
        max_source_length=args.max_source_length,
        max_target_length=args.max_target_length,
        max_samples=args.max_val_samples,
    )

    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        label_pad_token_id=-100,
        pad_to_multiple_of=8 if use_fp16 else None,
    )

    # Resume checkpoint resolution
    resume_from_checkpoint = None
    if args.resume:
        if args.resume == "latest":
            # Check for existing checkpoint directories
            ckpts = sorted(
                list(output_dir.glob("checkpoint-*")),
                key=lambda x: int(x.name.split("-")[-1]) if x.name.split("-")[-1].isdigit() else 0,
            )
            if ckpts:
                resume_from_checkpoint = str(ckpts[-1])
                logger.info(f"Found latest checkpoint to resume: {resume_from_checkpoint}")
            else:
                logger.warning(f"No previous checkpoints found in {output_dir}. Training from scratch.")
        else:
            resume_from_checkpoint = str(args.resume)
            logger.info(f"Resuming explicitly from checkpoint: {resume_from_checkpoint}")

    training_args = Seq2SeqTrainingArguments(
        output_dir=str(output_dir),
        logging_dir=str(runs_dir),
        evaluation_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=3,
        load_best_model_at_end=True,
        predict_with_generate=True,
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        num_train_epochs=args.epochs,
        weight_decay=args.weight_decay,
        warmup_ratio=args.warmup_ratio,
        fp16=use_fp16,
        seed=args.seed,
        logging_steps=50,
        report_to=["tensorboard"] if "tensorboard" in sys.modules else ["none"],
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    logger.info("Initiating model training on Colab...")
    train_result = trainer.train(resume_from_checkpoint=resume_from_checkpoint)

    # Save final best model & tokenizer directly to persistent export location
    logger.info(f"Saving final trained model to persistent export directory: {export_dir}...")
    trainer.save_model(str(export_dir))
    tokenizer.save_pretrained(str(export_dir))

    # Save training state metrics
    metrics = train_result.metrics
    trainer.save_metrics("train", metrics)
    trainer.save_state()

    logger.info(f"T5-small fine-tuning completed successfully. Model exported to: {export_dir}")


if __name__ == "__main__":
    main()
