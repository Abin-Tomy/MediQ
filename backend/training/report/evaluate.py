"""
evaluate.py — MediQ T5-Small Report Summarization Evaluation Pipeline

Evaluates fine-tuned T5-small models on held-out validation and test splits:
  - Computes genuine ROUGE-1, ROUGE-2, and ROUGE-L F1 scores.
  - Evaluates strictly on validation or test splits (training split explicitly rejected).
  - Never fabricates metrics when weights are absent.
  - Supports persistent Google Drive output directories.
  - Includes --validate_only mode for non-training preflight checks.

Usage Examples:
  # Preflight validation check (no weights required):
  python evaluate.py --validate_only

  # Full evaluation on test split after Colab training:
  python evaluate.py --split test --google_drive

  # Evaluate specific local checkpoint:
  python evaluate.py --checkpoint checkpoints/best --split validation
"""

import argparse
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import re
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import torch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("eval_t5_report")


# ---------------------------------------------------------------------------
# Genuine ROUGE Metric Computation (Pure-Python with evaluate Fallback)
# ---------------------------------------------------------------------------

def _tokenize_text_for_rouge(text: str) -> List[str]:
    """Tokenizes text into lowercase word tokens."""
    return re.findall(r"\b\w+\b", text.lower())


def _get_ngrams(tokens: List[str], n: int) -> List[Tuple[str, ...]]:
    """Extracts n-grams from a token list."""
    return [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def _lcs_length(seq1: List[str], seq2: List[str]) -> int:
    """Computes length of the Longest Common Subsequence (LCS)."""
    m, n = len(seq1), len(seq2)
    if m == 0 or n == 0:
        return 0
    dp = [0] * (n + 1)
    for i in range(1, m + 1):
        prev = 0
        for j in range(1, n + 1):
            temp = dp[j]
            if seq1[i - 1] == seq2[j - 1]:
                dp[j] = prev + 1
            else:
                dp[j] = max(dp[j], dp[j - 1])
            prev = temp
    return dp[n]


def compute_rouge_scores(predictions: List[str], references: List[str]) -> Dict[str, float]:
    """
    Computes ROUGE-1, ROUGE-2, and ROUGE-L F1 scores across prediction and reference pairs.
    Prefers Hugging Face evaluate/rouge_score if available; falls back to exact pure-Python calculation.
    """
    # Attempt HF evaluate if installed
    try:
        import evaluate
        rouge_metric = evaluate.load("rouge")
        results = rouge_metric.compute(predictions=predictions, references=references, use_stemmer=True)
        return {
            "rouge1": round(float(results["rouge1"]) * 100, 2),
            "rouge2": round(float(results["rouge2"]) * 100, 2),
            "rougeL": round(float(results["rougeL"]) * 100, 2),
        }
    except Exception:
        pass

    # Pure Python exact n-gram and LCS computation
    r1_f1_list, r2_f1_list, rl_f1_list = [], [], []

    for pred, ref in zip(predictions, references):
        pred_toks = _tokenize_text_for_rouge(pred)
        ref_toks = _tokenize_text_for_rouge(ref)

        # ROUGE-1
        ref_1 = Counter_dict = {}
        for t in ref_toks:
            Counter_dict[t] = Counter_dict.get(t, 0) + 1
        pred_1 = {}
        for t in pred_toks:
            pred_1[t] = pred_1.get(t, 0) + 1

        overlap1 = sum(min(count, Counter_dict.get(t, 0)) for t, count in pred_1.items())
        p1 = overlap1 / len(pred_toks) if pred_toks else 0.0
        r1 = overlap1 / len(ref_toks) if ref_toks else 0.0
        f1 = (2 * p1 * r1) / (p1 + r1) if (p1 + r1) > 0 else 0.0
        r1_f1_list.append(f1)

        # ROUGE-2
        pred_2 = _get_ngrams(pred_toks, 2)
        ref_2 = _get_ngrams(ref_toks, 2)
        ref_2_counts: Dict[Tuple[str, ...], int] = {}
        for bg in ref_2:
            ref_2_counts[bg] = ref_2_counts.get(bg, 0) + 1
        pred_2_counts: Dict[Tuple[str, ...], int] = {}
        for bg in pred_2:
            pred_2_counts[bg] = pred_2_counts.get(bg, 0) + 1

        overlap2 = sum(min(count, ref_2_counts.get(bg, 0)) for bg, count in pred_2_counts.items())
        p2 = overlap2 / len(pred_2) if pred_2 else 0.0
        r2 = overlap2 / len(ref_2) if ref_2 else 0.0
        f2 = (2 * p2 * r2) / (p2 + r2) if (p2 + r2) > 0 else 0.0
        r2_f1_list.append(f2)

        # ROUGE-L
        lcs = _lcs_length(pred_toks, ref_toks)
        pl = lcs / len(pred_toks) if pred_toks else 0.0
        rl = lcs / len(ref_toks) if ref_toks else 0.0
        fl = (2 * pl * rl) / (pl + rl) if (pl + rl) > 0 else 0.0
        rl_f1_list.append(fl)

    mean_r1 = (sum(r1_f1_list) / len(r1_f1_list) * 100) if r1_f1_list else 0.0
    mean_r2 = (sum(r2_f1_list) / len(r2_f1_list) * 100) if r2_f1_list else 0.0
    mean_rl = (sum(rl_f1_list) / len(rl_f1_list) * 100) if rl_f1_list else 0.0

    return {
        "rouge1": round(mean_r1, 2),
        "rouge2": round(mean_r2, 2),
        "rougeL": round(mean_rl, 2),
    }


# ---------------------------------------------------------------------------
# Split Evaluation Execution
# ---------------------------------------------------------------------------

def evaluate_checkpoint(
    checkpoint_path: Path,
    data_dir: Path,
    split: str,
    prefix: str = "summarize: ",
    max_source_length: int = 512,
    max_target_length: int = 128,
    num_beams: int = 4,
    batch_size: int = 8,
    max_eval_samples: Optional[int] = None,
    output_eval_dir: Optional[Path] = None,
    device: str = "auto",
) -> Dict[str, Any]:
    """
    Runs generation and computes genuine ROUGE metrics on a specific split.
    """
    if split not in ("validation", "test"):
        raise ValueError(
            f"Invalid evaluation split: '{split}'. "
            "Evaluations must be run strictly on 'validation' or 'test' sets. "
            "Never evaluate on 'train'."
        )

    jsonl_file = data_dir / split / "data.jsonl"
    if not jsonl_file.exists():
        raise FileNotFoundError(f"Evaluation dataset file not found: {jsonl_file}")

    from transformers import AutoTokenizer, T5ForConditionalGeneration

    if device == "auto":
        target_device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        target_device = device

    logger.info(f"Loading checkpoint for evaluation: {checkpoint_path}...")
    tokenizer = AutoTokenizer.from_pretrained(checkpoint_path)
    model = T5ForConditionalGeneration.from_pretrained(checkpoint_path).to(target_device)
    model.eval()

    logger.info(f"Evaluating on '{split}' split ({jsonl_file.name}). Target device: {target_device.upper()}...")

    articles: List[str] = []
    references: List[str] = []

    with open(jsonl_file, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if max_eval_samples and idx >= max_eval_samples:
                break
            d = json.loads(line)
            articles.append(d.get("article", "").strip())
            references.append(d.get("abstract", "").strip())

    total_samples = len(articles)
    logger.info(f"Loaded {total_samples:,} samples from '{split}' for generation and ROUGE scoring...")

    predictions: List[str] = []
    t_start = time.time()

    for i in range(0, total_samples, batch_size):
        batch_texts = [prefix + t for t in articles[i : i + batch_size]]
        inputs = tokenizer(
            batch_texts,
            max_length=max_source_length,
            truncation=True,
            padding=True,
            return_tensors="pt",
        ).to(target_device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=max_target_length,
                min_length=30,
                num_beams=num_beams,
                length_penalty=1.0,
                no_repeat_ngram_size=3,
                early_stopping=True,
            )

        decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)
        predictions.extend(decoded)

        if (i // batch_size + 1) % 10 == 0 or (i + batch_size >= total_samples):
            logger.info(f"Processed {len(predictions):,} / {total_samples:,} samples...")

    elapsed = time.time() - t_start
    logger.info(f"Generation completed in {elapsed:.2f}s ({total_samples / elapsed:.2f} samples/sec)")

    # Compute genuine ROUGE metrics
    logger.info("Computing ROUGE-1, ROUGE-2, and ROUGE-L scores...")
    rouge_results = compute_rouge_scores(predictions, references)

    logger.info("=" * 60)
    logger.info(f"EVALUATION RESULTS [{split.upper()} SET] (n={total_samples:,}):")
    logger.info(f"  ROUGE-1 F1 : {rouge_results['rouge1']:.2f}%")
    logger.info(f"  ROUGE-2 F1 : {rouge_results['rouge2']:.2f}%")
    logger.info(f"  ROUGE-L F1 : {rouge_results['rougeL']:.2f}%")
    logger.info("=" * 60)

    eval_payload = {
        "model_checkpoint": str(checkpoint_path),
        "split": split,
        "sample_count": total_samples,
        "metrics": rouge_results,
        "generation_config": {
            "max_source_length": max_source_length,
            "max_target_length": max_target_length,
            "num_beams": num_beams,
            "task_prefix": prefix,
        },
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "limitations_notice": "Trained on scientific biomedical literature; not clinically validated for patient health records.",
    }

    if output_eval_dir:
        output_eval_dir.mkdir(parents=True, exist_ok=True)
        out_file = output_eval_dir / f"eval_{split}_metrics.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(eval_payload, f, indent=2)
        logger.info(f"Evaluation metrics saved to: {out_file}")

    return eval_payload


# ---------------------------------------------------------------------------
# CLI Parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="MediQ T5-Small Report Summarization Evaluation Pipeline."
    )
    base_dir = Path(__file__).resolve().parent

    p.add_argument(
        "--checkpoint",
        type=str,
        default=None,
        help="Path to trained model checkpoint folder (defaults to checkpoints/best or exports)",
    )
    p.add_argument(
        "--data_dir",
        type=Path,
        default=base_dir / "processed",
        help="Path to processed dataset directory",
    )
    p.add_argument(
        "--split",
        type=str,
        default="test",
        choices=["validation", "test"],
        help="Evaluation split: 'test' (final benchmark) or 'validation' (tuning)",
    )
    p.add_argument(
        "--max_samples",
        type=int,
        default=None,
        help="Optional ceiling on samples to evaluate",
    )
    p.add_argument(
        "--batch_size",
        type=int,
        default=8,
        help="Evaluation batch size",
    )
    p.add_argument(
        "--num_beams",
        type=int,
        default=4,
        help="Beam search width for decoding",
    )
    p.add_argument(
        "--google_drive",
        action="store_true",
        help="Look for checkpoint and save results to Google Drive",
    )
    p.add_argument(
        "--drive_root",
        type=Path,
        default=Path("/content/drive/MyDrive/MediQ/training/report"),
        help="Root path on Google Drive",
    )
    p.add_argument(
        "--output_eval_dir",
        type=Path,
        default=None,
        help="Directory to save evaluation JSON results",
    )
    p.add_argument(
        "--validate_only",
        action="store_true",
        help="Verify evaluation pipeline dependencies, dataset splits, and paths without running inference",
    )
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent

    # Determine default checkpoint path
    if args.checkpoint:
        ckpt_path = Path(args.checkpoint).resolve()
    elif args.google_drive:
        primary_ckpt = args.drive_root / "checkpoints" / "best"
        secondary_ckpt = args.drive_root / "exports" / "t5_small_summarizer"
        ckpt_path = primary_ckpt if primary_ckpt.exists() else secondary_ckpt
    else:
        primary_ckpt = base_dir / "checkpoints" / "best"
        secondary_ckpt = base_dir / "exports" / "t5_small_summarizer"
        ckpt_path = primary_ckpt if primary_ckpt.exists() else secondary_ckpt

    # Determine output evaluation directory
    if args.output_eval_dir:
        eval_dir = args.output_eval_dir
    elif args.google_drive:
        eval_dir = args.drive_root / "evaluation"
    else:
        eval_dir = base_dir / "evaluation"

    # Preflight validation check
    if args.validate_only:
        logger.info("=== Preflight Evaluation Check: MediQ T5-Small Report Pipeline ===")
        logger.info(f"  Target dataset dir    : {args.data_dir}")
        logger.info(f"  Target split          : {args.split}")
        logger.info(f"  Target checkpoint     : {ckpt_path}")
        logger.info(f"  Evaluation output dir : {eval_dir}")

        split_file = args.data_dir / args.split / "data.jsonl"
        if not split_file.exists():
            raise FileNotFoundError(f"Target split file does not exist: {split_file}")
        logger.info(f"  Target split verified : {split_file.name} ({split_file.stat().st_size / (1024*1024):.2f} MB)")

        model_status = "EXISTS" if ckpt_path.exists() else "AWAITING_TRAINING (cleanly detected)"
        logger.info(f"  Model checkpoint      : {model_status}")
        logger.info("EVALUATION PIPELINE VALIDATION PASSED. Exiting without execution per --validate_only.")
        return

    # Non-preflight: strictly verify trained model exists
    if not ckpt_path.exists():
        logger.error(
            f"Cannot run evaluation: trained model checkpoint not found at: {ckpt_path}\n"
            "Please run model training in Google Colab first:\n"
            "    python train.py --google_drive"
        )
        sys.exit(1)

    evaluate_checkpoint(
        checkpoint_path=ckpt_path,
        data_dir=args.data_dir,
        split=args.split,
        num_beams=args.num_beams,
        batch_size=args.batch_size,
        max_eval_samples=args.max_samples,
        output_eval_dir=eval_dir,
    )


if __name__ == "__main__":
    main()
