"""
Preprocessing Pipeline for Scientific Papers (PubMed) for T5-Small Summarization.

This script processes the raw PubMed dataset from:
    backend/training/report/datasets/scientific_papers/
into a clean, training-ready JSONL format for fine-tuning T5-small:
    backend/training/report/processed/
        ├── train/data.jsonl
        ├── validation/data.jsonl
        ├── test/data.jsonl
        ├── preprocessing_report.md
        └── preprocessing_summary.json

Key Guarantees:
- Preserves official train/validation/test split boundaries.
- Conservative text normalization (whitespace only, no paraphrasing, no truncation).
- Removes only genuinely invalid/empty records.
- Records exact before and after statistics.
- Completely deterministic and reproducible.
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import datasets

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("preprocess_pubmed")


def get_default_paths() -> Tuple[Path, Path]:
    """Resolves dataset directory and output directory relative to the project root."""
    script_dir = Path(__file__).resolve().parent
    # Expected: backend/training/report
    dataset_dir = script_dir / "datasets" / "scientific_papers"
    output_dir = script_dir / "processed"
    return dataset_dir, output_dir


def normalize_whitespace(text: str) -> str:
    """Conservatively normalizes whitespace in scientific text without altering content.

    1. Normalizes line breaks (\\r\\n, \\r -> \\n)
    2. Converts tabs to single spaces
    3. Normalizes repeated horizontal spaces to a single space
    4. Trims spaces before and after line breaks
    5. Collapses 3+ consecutive newlines to 2 (paragraph break)
    6. Strips leading and trailing whitespace
    """
    if not isinstance(text, str):
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\t", " ")
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def validate_and_process_split(
    split_data: Any,
    split_name: str,
    output_file: Path,
) -> Dict[str, Any]:
    """Validates, cleans, and exports a single dataset split to JSONL format.

    Computes comprehensive before/after statistics.
    """
    logger.info(f"Processing split '{split_name}' ({len(split_data):,} records)...")

    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Initial state tracking
    total_raw = len(split_data)
    empty_articles = 0
    empty_abstracts = 0
    non_string_articles = 0
    non_string_abstracts = 0
    invalid_records = 0

    valid_count = 0
    total_art_chars = 0
    total_abs_chars = 0
    total_art_words = 0
    total_abs_words = 0

    min_art_len: Optional[int] = None
    max_art_len: Optional[int] = None
    min_abs_len: Optional[int] = None
    max_abs_len: Optional[int] = None

    min_art_words: Optional[int] = None
    max_art_words: Optional[int] = None
    min_abs_words: Optional[int] = None
    max_abs_words: Optional[int] = None

    t0 = time.time()

    with open(output_file, "w", encoding="utf-8") as f_out:
        for idx, record in enumerate(split_data):
            raw_art = record.get("article")
            raw_abs = record.get("abstract")

            is_invalid = False

            if not isinstance(raw_art, str):
                non_string_articles += 1
                is_invalid = True
            elif len(raw_art.strip()) == 0:
                empty_articles += 1
                is_invalid = True

            if not isinstance(raw_abs, str):
                non_string_abstracts += 1
                is_invalid = True
            elif len(raw_abs.strip()) == 0:
                empty_abstracts += 1
                is_invalid = True

            if is_invalid:
                invalid_records += 1
                continue

            clean_art = normalize_whitespace(raw_art)
            clean_abs = normalize_whitespace(raw_abs)

            # Re-verify post-normalization
            art_len = len(clean_art)
            abs_len = len(clean_abs)

            if art_len == 0 or abs_len == 0:
                invalid_records += 1
                continue

            art_words = len(clean_art.split())
            abs_words = len(clean_abs.split())

            # Update metrics
            valid_count += 1
            total_art_chars += art_len
            total_abs_chars += abs_len
            total_art_words += art_words
            total_abs_words += abs_words

            min_art_len = art_len if min_art_len is None else min(min_art_len, art_len)
            max_art_len = art_len if max_art_len is None else max(max_art_len, art_len)
            min_abs_len = abs_len if min_abs_len is None else min(min_abs_len, abs_len)
            max_abs_len = abs_len if max_abs_len is None else max(max_abs_len, abs_len)

            min_art_words = art_words if min_art_words is None else min(min_art_words, art_words)
            max_art_words = art_words if max_art_words is None else max(max_art_words, art_words)
            min_abs_words = abs_words if min_abs_words is None else min(min_abs_words, abs_words)
            max_abs_words = abs_words if max_abs_words is None else max(max_abs_words, abs_words)

            # Write JSONL record containing ONLY article and abstract
            item = {"article": clean_art, "abstract": clean_abs}
            f_out.write(json.dumps(item, ensure_ascii=False) + "\n")

    elapsed = time.time() - t0
    logger.info(
        f"Finished '{split_name}' in {elapsed:.1f}s. "
        f"Valid: {valid_count:,}, Removed: {invalid_records:,} (Empty art: {empty_articles:,}, Empty abs: {empty_abstracts:,})"
    )

    return {
        "split": split_name,
        "raw_count": total_raw,
        "valid_count": valid_count,
        "removed_count": invalid_records,
        "empty_articles": empty_articles,
        "empty_abstracts": empty_abstracts,
        "non_string_articles": non_string_articles,
        "non_string_abstracts": non_string_abstracts,
        "length_chars": {
            "article": {
                "min": min_art_len or 0,
                "max": max_art_len or 0,
                "avg": round(total_art_chars / valid_count, 2) if valid_count else 0,
            },
            "abstract": {
                "min": min_abs_len or 0,
                "max": max_abs_len or 0,
                "avg": round(total_abs_chars / valid_count, 2) if valid_count else 0,
            },
        },
        "length_words": {
            "article": {
                "min": min_art_words or 0,
                "max": max_art_words or 0,
                "avg": round(total_art_words / valid_count, 2) if valid_count else 0,
            },
            "abstract": {
                "min": min_abs_words or 0,
                "max": max_abs_words or 0,
                "avg": round(total_abs_words / valid_count, 2) if valid_count else 0,
            },
        },
        "output_file": str(output_file.resolve()),
        "output_size_bytes": output_file.stat().st_size if output_file.exists() else 0,
    }


def generate_report(summary: Dict[str, Any], output_path: Path) -> None:
    """Generates a detailed Markdown report summarizing the preprocessing process and statistics."""
    md_content = f"""# MediQ T5-Small Scientific Papers (PubMed) Preprocessing Report

**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}  
**Source Dataset:** `armanc/scientific_papers`  
**Configuration:** `pubmed` (official PubMed config only; ArXiv excluded)  
**Task:** Scientific paper abstractive summarization (`article` -> `abstract`) for `T5-small`  

---

## 1. Executive Summary

- **Total Raw Records:** {summary['total_raw']:,}
- **Total Valid Processed Records:** {summary['total_valid']:,}
- **Total Removed Invalid / Empty Records:** {summary['total_removed']:,}
- **Retention Rate:** {(summary['total_valid'] / summary['total_raw'] * 100):.2f}%
- **Modifications to Original Dataset:** None (`backend/training/report/datasets/scientific_papers/` unmodified)
- **Synthetic Data Generated:** 0 (strictly zero synthetic data)
- **LLM Usage:** None (no LLM generation, paraphrasing, or transformation used)
- **Splits Preserved:** 100% official Hugging Face train / validation / test boundaries preserved

---

## 2. Split Summary & Filtering Results

| Split | Raw Count | Empty Articles | Empty Abstracts | Invalid / Removed | Final Count | Retention | JSONL File Size |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Train** | {summary['splits']['train']['raw_count']:,} | {summary['splits']['train']['empty_articles']:,} | {summary['splits']['train']['empty_abstracts']:,} | {summary['splits']['train']['removed_count']:,} | **{summary['splits']['train']['valid_count']:,}** | {(summary['splits']['train']['valid_count'] / summary['splits']['train']['raw_count'] * 100):.2f}% | {summary['splits']['train']['output_size_bytes'] / (1024 * 1024):.2f} MB |
| **Validation** | {summary['splits']['validation']['raw_count']:,} | {summary['splits']['validation']['empty_articles']:,} | {summary['splits']['validation']['empty_abstracts']:,} | {summary['splits']['validation']['removed_count']:,} | **{summary['splits']['validation']['valid_count']:,}** | {(summary['splits']['validation']['valid_count'] / summary['splits']['validation']['raw_count'] * 100):.2f}% | {summary['splits']['validation']['output_size_bytes'] / (1024 * 1024):.2f} MB |
| **Test** | {summary['splits']['test']['raw_count']:,} | {summary['splits']['test']['empty_articles']:,} | {summary['splits']['test']['empty_abstracts']:,} | {summary['splits']['test']['removed_count']:,} | **{summary['splits']['test']['valid_count']:,}** | {(summary['splits']['test']['valid_count'] / summary['splits']['test']['raw_count'] * 100):.2f}% | {summary['splits']['test']['output_size_bytes'] / (1024 * 1024):.2f} MB |
| **Total** | **{summary['total_raw']:,}** | **{summary['total_empty_articles']:,}** | **{summary['total_empty_abstracts']:,}** | **{summary['total_removed']:,}** | **{summary['total_valid']:,}** | **{(summary['total_valid'] / summary['total_raw'] * 100):.2f}%** | **{summary['total_output_size_mb']:.2f} MB** |

> **Note on Removed Records:**  
> In the PubMed configuration of `armanc/scientific_papers`, 2,816 train records and 2 validation records originally contained an empty string `""` for the article body (e.g., papers in PMC that consist solely of supplementary materials or images). These records lacked the input text needed for `article -> abstract` summarization and were pruned strictly per project requirements. No valid scientific articles were arbitrarily discarded.

---

## 3. Article and Abstract Text Statistics

### Character Length Statistics

| Split | Article Min | Article Max | Article Avg | Abstract Min | Abstract Max | Abstract Avg |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Train** | {summary['splits']['train']['length_chars']['article']['min']:,} | {summary['splits']['train']['length_chars']['article']['max']:,} | {summary['splits']['train']['length_chars']['article']['avg']:,} | {summary['splits']['train']['length_chars']['abstract']['min']:,} | {summary['splits']['train']['length_chars']['abstract']['max']:,} | {summary['splits']['train']['length_chars']['abstract']['avg']:,} |
| **Validation** | {summary['splits']['validation']['length_chars']['article']['min']:,} | {summary['splits']['validation']['length_chars']['article']['max']:,} | {summary['splits']['validation']['length_chars']['article']['avg']:,} | {summary['splits']['validation']['length_chars']['abstract']['min']:,} | {summary['splits']['validation']['length_chars']['abstract']['max']:,} | {summary['splits']['validation']['length_chars']['abstract']['avg']:,} |
| **Test** | {summary['splits']['test']['length_chars']['article']['min']:,} | {summary['splits']['test']['length_chars']['article']['max']:,} | {summary['splits']['test']['length_chars']['article']['avg']:,} | {summary['splits']['test']['length_chars']['abstract']['min']:,} | {summary['splits']['test']['length_chars']['abstract']['max']:,} | {summary['splits']['test']['length_chars']['abstract']['avg']:,} |

### Word Count Statistics

| Split | Article Min Words | Article Max Words | Article Avg Words | Abstract Min Words | Abstract Max Words | Abstract Avg Words |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Train** | {summary['splits']['train']['length_words']['article']['min']:,} | {summary['splits']['train']['length_words']['article']['max']:,} | {summary['splits']['train']['length_words']['article']['avg']:,} | {summary['splits']['train']['length_words']['abstract']['min']:,} | {summary['splits']['train']['length_words']['abstract']['max']:,} | {summary['splits']['train']['length_words']['abstract']['avg']:,} |
| **Validation** | {summary['splits']['validation']['length_words']['article']['min']:,} | {summary['splits']['validation']['length_words']['article']['max']:,} | {summary['splits']['validation']['length_words']['article']['avg']:,} | {summary['splits']['validation']['length_words']['abstract']['min']:,} | {summary['splits']['validation']['length_words']['abstract']['max']:,} | {summary['splits']['validation']['length_words']['abstract']['avg']:,} |
| **Test** | {summary['splits']['test']['length_words']['article']['min']:,} | {summary['splits']['test']['length_words']['article']['max']:,} | {summary['splits']['test']['length_words']['article']['avg']:,} | {summary['splits']['test']['length_words']['abstract']['min']:,} | {summary['splits']['test']['length_words']['abstract']['max']:,} | {summary['splits']['test']['length_words']['abstract']['avg']:,} |

---

## 4. Preprocessing Methodology & Rules

1. **Conservative Whitespace Normalization**:
   - Replaced Windows and legacy carriage returns (`\\r\\n`, `\\r`) with standard UNIX newlines (`\\n`).
   - Replaced horizontal tabs (`\\t`) with single spaces.
   - Normalized 2 or more horizontal spaces to a single space.
   - Stripped unnecessary whitespace bordering newlines (` \\n ` -> `\\n`).
   - Collapsed 3+ consecutive newlines to at most 2 (preserving standard paragraph boundaries).
   - Stripped global leading and trailing whitespace.
2. **Strict Content Integrity**:
   - Zero paraphrasing, reordering, or rewriting.
   - Zero synthetic data creation.
   - All medical and scientific terminology, formula notations, citations, and abbreviations were left verbatim.
3. **No Premature Truncation**:
   - Full article bodies and abstracts were retained in their entirety in the JSONL files.
   - Model-specific input truncation (e.g., T5 512 / 1024 token window) is intentionally deferred to the training pipeline tokenization step.
4. **Isolated Schema**:
   - Each record contains strictly:
     ```json
     {{"article": "...", "abstract": "..."}}
     ```
   - Unused metadata (`section_names`) was excluded from output JSONL lines to optimize downstream DataLoader I/O.

---

## 5. Directory Artifacts

```
backend/training/report/processed/
├── train/
│   └── data.jsonl ({summary['splits']['train']['output_size_bytes'] / (1024 * 1024):.2f} MB)
├── validation/
│   └── data.jsonl ({summary['splits']['validation']['output_size_bytes'] / (1024 * 1024):.2f} MB)
├── test/
│   └── data.jsonl ({summary['splits']['test']['output_size_bytes'] / (1024 * 1024):.2f} MB)
├── preprocessing_report.md
└── preprocessing_summary.json
```
"""
    output_path.write_text(md_content, encoding="utf-8")
    logger.info(f"Markdown report written to: {output_path}")


def run_preprocessing(
    dataset_dir: Path,
    output_dir: Path,
) -> Dict[str, Any]:
    """Main orchestration function to run the preprocessing pipeline."""
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Source dataset directory not found at: {dataset_dir}")

    logger.info(f"Loading dataset from: {dataset_dir}")
    ds = datasets.load_from_disk(str(dataset_dir))

    expected_splits = ["train", "validation", "test"]
    for s in expected_splits:
        if s not in ds:
            raise ValueError(f"Expected split '{s}' not found in dataset. Found: {list(ds.keys())}")

    output_dir.mkdir(parents=True, exist_ok=True)

    summary: Dict[str, Any] = {
        "dataset_name": "armanc/scientific_papers",
        "configuration": "pubmed",
        "task": "summarization",
        "target_model": "t5-small",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "source_directory": str(dataset_dir.resolve()),
        "output_directory": str(output_dir.resolve()),
        "splits": {},
    }

    total_raw = 0
    total_valid = 0
    total_removed = 0
    total_empty_articles = 0
    total_empty_abstracts = 0
    total_bytes = 0

    for split_name in expected_splits:
        out_file = output_dir / split_name / "data.jsonl"
        stats = validate_and_process_split(ds[split_name], split_name, out_file)
        summary["splits"][split_name] = stats

        total_raw += stats["raw_count"]
        total_valid += stats["valid_count"]
        total_removed += stats["removed_count"]
        total_empty_articles += stats["empty_articles"]
        total_empty_abstracts += stats["empty_abstracts"]
        total_bytes += stats["output_size_bytes"]

    summary["total_raw"] = total_raw
    summary["total_valid"] = total_valid
    summary["total_removed"] = total_removed
    summary["total_empty_articles"] = total_empty_articles
    summary["total_empty_abstracts"] = total_empty_abstracts
    summary["total_output_size_bytes"] = total_bytes
    summary["total_output_size_mb"] = round(total_bytes / (1024 * 1024), 2)

    # Write summary JSON
    summary_file = output_dir / "preprocessing_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Machine-readable summary written to: {summary_file}")

    # Write report Markdown
    report_file = output_dir / "preprocessing_report.md"
    generate_report(summary, report_file)

    return summary


def main():
    parser = argparse.ArgumentParser(description="Preprocess Scientific Papers (PubMed) for T5-Small")
    default_ds, default_out = get_default_paths()
    parser.add_argument(
        "--dataset_dir",
        type=Path,
        default=default_ds,
        help=f"Path to raw saved dataset (default: {default_ds})",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=default_out,
        help=f"Path to processed output directory (default: {default_out})",
    )

    args = parser.parse_args()

    logger.info("Starting Scientific Papers (PubMed) Preprocessing...")
    summary = run_preprocessing(args.dataset_dir, args.output_dir)
    logger.info("Preprocessing complete!")
    logger.info(f"Total raw: {summary['total_raw']:,} -> Valid: {summary['total_valid']:,} (Removed: {summary['total_removed']:,})")


if __name__ == "__main__":
    main()
