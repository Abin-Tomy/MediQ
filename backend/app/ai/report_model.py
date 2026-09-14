"""
T5-small Medical Report Analysis Model Service.

Responsible exclusively for T5-small summarisation of medical reports.

Future processing pipeline (not implemented in this step):
  1. PDF text extraction via PyMuPDF (already in requirements.txt)
  2. Scanned document OCR via Tesseract (already in requirements.txt)
  3. T5-small summarisation of extracted text

Current state (Stage 3 – Step 1)
---------------------------------
The trained model artefacts do not yet exist.  This module defines the full
inference contract so the API layer never needs to change when real weights
are deployed.

Input contract
--------------
    text : str – Extracted report text (plain text, not raw PDF bytes)

Output contract
---------------
    {
        "model":     "t5_medical_report",
        "available": false,
        "summary":   "",
        "notes":     "<reason>"
    }

Safety rules
------------
* Do NOT fabricate medical summaries when the model is unavailable.
* Do NOT implement PDF/OCR processing in this step.
* summary must be an empty string when unavailable.
"""

import logging
import os
from dataclasses import dataclass

from app.ai.base import BaseAIModel
from app.ai.config import REPORT_MODEL_PATH

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Typed result objects
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ReportInferenceResult:
    """
    Full output from the T5-small medical report model.

    All consumers must check ``available`` before using ``summary``.
    When ``available`` is False, ``summary`` is guaranteed to be an empty string.
    """

    model: str = "t5_medical_report"
    available: bool = False
    summary: str = ""
    notes: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Model service
# ─────────────────────────────────────────────────────────────────────────────

_UNAVAILABLE_NOTE = (
    "The T5-small medical report analysis model has not been trained or deployed yet. "
    "No summary is available.  Report summarisation will become active once trained "
    "artefacts are placed at the configured model path."
)

_REQUIRED_ARTEFACTS = [
    "config.json",         # HuggingFace model config
    "tokenizer.json",      # Tokenizer vocabulary
    "spiece.model",        # SentencePiece tokenizer (T5-specific)
]


class T5ReportModel(BaseAIModel):
    """
    Service wrapper for the fine-tuned T5-small medical report summariser.

    Lifecycle
    ---------
    Instantiation  → no I/O, no memory allocation
    load()         → checks for artefact files; loads model if present
    infer()        → runs summarisation if available, otherwise safe empty response

    Future PDF / OCR pre-processing
    --------------------------------
    Text extraction from PDF and scanned images will be handled by a separate
    pre-processing utility (PyMuPDF + Tesseract) before the extracted text is
    passed to this service's infer() method.  That utility is NOT part of
    Stage 3 Step 1.
    """

    def __init__(self) -> None:
        super().__init__(
            model_name="t5_medical_report",
            model_path=REPORT_MODEL_PATH,
        )
        # The actual HuggingFace summarisation pipeline — set after load()
        self._pipeline = None

    # ─────────────────────────────────────────────────────────────────────────
    # load()
    # ─────────────────────────────────────────────────────────────────────────

    def load(self) -> None:
        """
        Attempt to load T5-small model artefacts from the configured path.

        Idempotent — repeated calls are no-ops when already loaded.
        Missing artefacts are handled gracefully (no exception raised).

        When the trained model is ready, this method should:
          1. Import transformers.pipeline
          2. Load the tokenizer and model from self._model_path
          3. Create a "summarization" pipeline
          4. Set self._pipeline, self._available, self._loaded
        """
        if self._loaded:
            return  # idempotent guard

        self._log_load_attempt()

        if not os.path.isdir(self._model_path):
            self._log_unavailable(
                "model directory not found at configured path"
            )
            return

        # Check both configured directory and 'latest/' subdirectory
        candidate_dirs = [
            os.path.join(self._model_path, "latest"),
            self._model_path,
        ]
        resolved_dir = None
        required_check = ["config.json", "tokenizer.json"]

        for c_dir in candidate_dirs:
            if os.path.isdir(c_dir):
                missing = [
                    f for f in required_check
                    if not os.path.isfile(os.path.join(c_dir, f))
                ]
                if not missing:
                    resolved_dir = c_dir
                    break

        if resolved_dir is None:
            self._log_unavailable(
                f"required artefacts {required_check} missing at '{self._model_path}'"
            )
            return

        # ── FUTURE: real model loading goes here ──────────────────────────────
        # try:
        #     from transformers import pipeline
        #     self._pipeline = pipeline(
        #         "summarization",
        #         model=self._model_path,
        #         device=0 if AI_DEVICE == "cuda" else -1,
        #     )
        #     self._available = True
        #     self._loaded = True
        #     logger.info("T5 medical report model loaded successfully.")
        # except Exception as exc:
        #     logger.error("Failed to load T5 model: %s", exc)
        # ─────────────────────────────────────────────────────────────────────

        logger.info(
            "T5 report model artefacts found but inference is not yet wired "
            "(Stage 3 Step 2). Marking as unavailable."
        )

    # ─────────────────────────────────────────────────────────────────────────
    # infer()
    # ─────────────────────────────────────────────────────────────────────────

    def infer(self, text: str) -> ReportInferenceResult:
        """
        Run T5-small medical report summarisation.

        Parameters
        ----------
        text : str
            Plain-text content extracted from a medical report.
            PDF / OCR pre-processing must happen before this call.

        Returns
        -------
        ReportInferenceResult
            Always safe to consume — check ``available`` before using
            ``summary``.
        """
        if not self.is_available():
            return ReportInferenceResult(
                model="t5_medical_report",
                available=False,
                summary="",
                notes=_UNAVAILABLE_NOTE,
            )

        # ── FUTURE: real inference goes here ─────────────────────────────────
        # output = self._pipeline(
        #     text,
        #     max_length=256,
        #     min_length=40,
        #     do_sample=False,
        # )
        # return ReportInferenceResult(
        #     model="t5_medical_report",
        #     available=True,
        #     summary=output[0]["summary_text"],
        #     notes="T5 summarisation completed.",
        # )
        # ─────────────────────────────────────────────────────────────────────

        logger.warning(
            "T5 model marked available but pipeline is None — "
            "returning unavailable response."
        )
        return ReportInferenceResult(
            model="t5_medical_report",
            available=False,
            summary="",
            notes=_UNAVAILABLE_NOTE,
        )
