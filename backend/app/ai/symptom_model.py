"""
DistilBERT Symptom Analysis Model Service.

Responsible exclusively for the fine-tuned DistilBERT model that analyses
patient symptom text and returns ranked condition predictions.

Lifecycle
---------
Instantiation  → no I/O, no memory allocation
load()         → checks for artefact files; loads tokenizer and PyTorch model once
infer()        → runs inference under torch.no_grad() if available, otherwise returns safe unavailable response
status()       → returns safe status dict without exposing filesystem paths
"""

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional

from app.ai.base import BaseAIModel
from app.ai.config import AI_DEVICE, SYMPTOM_MODEL_PATH

logger = logging.getLogger(__name__)

# Malayalam Unicode block regex range: U+0D00 to U+0D7F
_MALAYALAM_CHAR_PATTERN = re.compile(r"[\u0d00-\u0d7f]")


# ─────────────────────────────────────────────────────────────────────────────
# Typed result objects
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ConditionPrediction:
    """Single condition entry in the DistilBERT output."""

    condition: str
    confidence: float  # 0.0 – 1.0; populated solely with real model softmax probability


@dataclass
class SymptomInferenceResult:
    """
    Full output from the DistilBERT symptom model.

    All consumers must check ``available`` before using ``predictions``.
    """

    model: str = "distilbert_symptom"
    available: bool = False
    predictions: List[ConditionPrediction] = field(default_factory=list)
    notes: str = ""
    model_version: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Model service
# ─────────────────────────────────────────────────────────────────────────────

_UNAVAILABLE_NOTE = (
    "The DistilBERT symptom analysis model has not been trained or deployed yet. "
    "No predictions are available. The rule-based placeholder at "
    "POST /analyse/symptoms remains active for clinical decision support."
)

_MODEL_VERSION = "distilbert-symptom-v1"


class DistilBERTSymptomModel(BaseAIModel):
    """
    Service wrapper for the fine-tuned DistilBERT symptom classifier.

    Loads the tokenizer and sequence classification model once at application startup.
    Inference is strictly evaluated under torch.no_grad() and outputs ranked probabilities.
    """

    def __init__(self) -> None:
        super().__init__(
            model_name="distilbert_symptom",
            model_path=SYMPTOM_MODEL_PATH,
        )
        self._model_version: str = _MODEL_VERSION
        self._tokenizer = None
        self._model = None
        self._id2label: dict[int, str] = {}
        self._label2id: dict[str, int] = {}
        self._device = None

    # ─────────────────────────────────────────────────────────────────────────
    # load()
    # ─────────────────────────────────────────────────────────────────────────

    def load(self) -> None:
        """
        Attempt to load DistilBERT model artefacts from the configured path.

        Idempotent — repeated calls are no-ops when already loaded.
        Missing artefacts are handled gracefully (no exception raised).
        """
        if self._loaded:
            return  # idempotent guard

        self._log_load_attempt()

        # 1. Check directory existence
        if not os.path.isdir(self._model_path):
            self._log_unavailable("model directory not found at configured path")
            return

        # Check both configured directory and subdirectories ('latest/', 'stage1/')
        candidate_dirs = [
            os.path.join(self._model_path, "latest"),
            os.path.join(self._model_path, "stage1"),
            self._model_path,
        ]
        resolved_path = None
        for candidate in candidate_dirs:
            if not os.path.isdir(candidate):
                continue
            config_ok = os.path.isfile(os.path.join(candidate, "config.json"))
            label_ok = os.path.isfile(os.path.join(candidate, "label_mapping.json"))
            has_tok = any(
                os.path.isfile(os.path.join(candidate, f))
                for f in ("tokenizer.json", "vocab.txt")
            )
            has_wt = any(
                os.path.isfile(os.path.join(candidate, f))
                for f in ("model.safetensors", "pytorch_model.bin")
            )
            if config_ok and label_ok and has_tok and has_wt:
                resolved_path = candidate
                break

        if not resolved_path:
            self._log_unavailable("model artefacts (config, label_mapping, tokenizer, weights) missing from model directory")
            return

        # 3. Load artefacts safely
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            # Determine device safely
            if AI_DEVICE == "cuda" and torch.cuda.is_available():
                self._device = torch.device("cuda")
            else:
                self._device = torch.device("cpu")

            # Load label mapping
            label_map_path = os.path.join(resolved_path, "label_mapping.json")
            with open(label_map_path, "r", encoding="utf-8") as f:
                mapping_data = json.load(f)
            self._id2label = {int(k): v for k, v in mapping_data.get("id2label", {}).items()}
            self._label2id = {k: int(v) for k, v in mapping_data.get("label2id", {}).items()}

            # Load tokenizer and model
            logger.info("Loading DistilBERT tokenizer and weights from: %s", resolved_path)
            self._tokenizer = AutoTokenizer.from_pretrained(resolved_path)
            self._model = AutoModelForSequenceClassification.from_pretrained(resolved_path)
            self._model.to(self._device)
            self._model.eval()

            self._available = True
            self._loaded = True
            logger.info(
                "DistilBERT symptom model loaded successfully on device '%s' with %d classes.",
                self._device,
                len(self._id2label),
            )
        except Exception as exc:
            self._available = False
            self._loaded = False
            self._model = None
            self._tokenizer = None
            logger.error(
                "Failed to load DistilBERT symptom model from '%s': %s",
                self._model_path,
                exc,
                exc_info=True,
            )

    # ─────────────────────────────────────────────────────────────────────────
    # infer()
    # ─────────────────────────────────────────────────────────────────────────

    def infer(
        self, symptoms: str, language: str = "en", top_k: int = 5
    ) -> SymptomInferenceResult:
        """
        Run DistilBERT symptom inference.

        Parameters
        ----------
        symptoms : str
            Patient-reported symptom text.
        language : str
            ISO 639-1 code (e.g. "en").
        top_k : int
            Number of top ranked predictions to return (default: 5).

        Returns
        -------
        SymptomInferenceResult
            Always safe to consume — check ``available`` before using ``predictions``.
        """
        if not self.is_available():
            return SymptomInferenceResult(
                model="distilbert_symptom",
                available=False,
                predictions=[],
                notes=_UNAVAILABLE_NOTE,
                model_version=None,
            )

        # Defensive sanity check
        if self._model is None or self._tokenizer is None:
            logger.warning("DistilBERT marked available but model/tokenizer is None.")
            return SymptomInferenceResult(
                model="distilbert_symptom",
                available=False,
                predictions=[],
                notes=_UNAVAILABLE_NOTE,
                model_version=None,
            )

        # Handle non-English / Malayalam input safely
        norm_lang = (language or "en").strip().lower()
        if norm_lang == "ml" or bool(_MALAYALAM_CHAR_PATTERN.search(symptoms)):
            return SymptomInferenceResult(
                model="distilbert_symptom",
                available=True,
                predictions=[],
                notes=(
                    "Malayalam language input detected. Automated translation is scheduled for "
                    "a future batch. The English DistilBERT model currently accepts English symptoms."
                ),
                model_version=self._model_version,
            )

        clean_text = symptoms.strip().lower()
        if not clean_text:
            return SymptomInferenceResult(
                model="distilbert_symptom",
                available=True,
                predictions=[],
                notes="No symptom text provided for inference.",
                model_version=self._model_version,
            )

        try:
            import torch

            # Tokenize using the same preprocessing bounds as training
            inputs = self._tokenizer(
                clean_text,
                truncation=True,
                padding=True,
                max_length=128,
                return_tensors="pt",
            )
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            # Run inference without gradient computation
            with torch.no_grad():
                outputs = self._model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=-1).squeeze(0)

                k = max(1, min(top_k, len(probs)))
                top_values, top_indices = torch.topk(probs, k=k)

            predictions = []
            for score, idx in zip(top_values, top_indices):
                label_idx = idx.item()
                condition_name = self._id2label.get(label_idx, f"Condition_{label_idx}")
                confidence = round(score.item(), 4)
                predictions.append(
                    ConditionPrediction(condition=condition_name, confidence=confidence)
                )

            return SymptomInferenceResult(
                model="distilbert_symptom",
                available=True,
                predictions=predictions,
                notes="DistilBERT inference completed.",
                model_version=self._model_version,
            )

        except Exception as exc:
            logger.error("DistilBERT inference encountered an error: %s", exc, exc_info=True)
            return SymptomInferenceResult(
                model="distilbert_symptom",
                available=True,
                predictions=[],
                notes=f"Inference execution failed: {str(exc)}",
                model_version=self._model_version,
            )

    # ─────────────────────────────────────────────────────────────────────────
    # status()
    # ─────────────────────────────────────────────────────────────────────────

    def status(self) -> dict:
        """Return safe status dictionary without exposing filesystem paths."""
        base_status = super().status()
        base_status["model_version"] = self._model_version if self._available else None
        return base_status
