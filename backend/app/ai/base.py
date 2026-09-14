"""
Base AI Model Interface.

Defines the abstract contract that every concrete AI model service must satisfy.
The FastAPI route layer and the ModelManager communicate exclusively through this
interface — they never import DistilBERT, YOLOv8, or T5 classes directly.

Design goals
------------
* Consistent load / availability / status reporting across all three model types.
* Clear separation between the inference contract (this file) and implementation
  details (symptom_model.py, image_model.py, report_model.py).
* Safe by default: if a concrete model has not been loaded or its weights are
  missing, callers can detect this through is_available() before attempting
  inference.
"""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseAIModel(ABC):
    """
    Abstract base class for all MediQ AI model services.

    Concrete sub-classes implement load(), is_available(), and status().
    Each sub-class is also expected to expose its own typed ``infer()``
    method — the signature deliberately varies per model type (different
    inputs / outputs), so it is **not** declared abstract here.  Sub-classes
    must document their own infer() contract clearly.
    """

    def __init__(self, model_name: str, model_path: str) -> None:
        """
        Parameters
        ----------
        model_name:
            Human-readable identifier used in status and log messages
            (e.g. ``"distilbert_symptom"``).
        model_path:
            Filesystem path where the model artefacts are expected to be found.
            This value is used for existence checks; it is **never** exposed
            through API responses.
        """
        self._model_name: str = model_name
        self._model_path: str = model_path
        self._loaded: bool = False
        self._available: bool = False

    # ─────────────────────────────────────────────────────────────────────────
    # Abstract interface
    # ─────────────────────────────────────────────────────────────────────────

    @abstractmethod
    def load(self) -> None:
        """
        Attempt to load the model artefacts from ``self._model_path``.

        Contract:
        * Must be idempotent — calling load() on an already-loaded model is a no-op.
        * If artefacts are missing or corrupted, set ``self._available = False``
          and ``self._loaded = False``; do NOT raise an exception so the server
          can continue starting up.
        * If loading succeeds, set ``self._available = True``
          and ``self._loaded = True``.
        """

    # ─────────────────────────────────────────────────────────────────────────
    # Concrete helpers
    # ─────────────────────────────────────────────────────────────────────────

    def is_available(self) -> bool:
        """
        Return True only if the model weights exist and have been loaded
        successfully.  Use this before calling infer() to avoid runtime errors.
        """
        return self._available and self._loaded

    def status(self) -> dict:
        """
        Return a safe status dictionary suitable for inclusion in API responses.

        The dictionary intentionally omits the filesystem path so that internal
        directory structure is never leaked through the /ai/status endpoint.

        Returns
        -------
        dict with keys:
            model_name  (str)  – identifier string
            available   (bool) – True if weights are present and loaded
            loaded      (bool) – True if load() has successfully completed
        """
        return {
            "model_name": self._model_name,
            "available": self._available,
            "loaded": self._loaded,
        }

    def _log_load_attempt(self) -> None:
        """Helper: emit a consistent DEBUG log message before each load attempt."""
        logger.debug("Attempting to load model '%s'.", self._model_name)

    def _log_unavailable(self, reason: str = "") -> None:
        """Helper: emit a consistent INFO log when a model is not found."""
        logger.info(
            "Model '%s' is not available%s.",
            self._model_name,
            f" — {reason}" if reason else "",
        )
