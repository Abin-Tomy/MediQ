"""
AI Model Manager.

The ModelManager is the single co-ordination point for all AI model services.
The FastAPI application holds one module-level instance (created in
app/ai/__init__.py) so that:

  * Models are initialised once at application startup via initialize().
  * No model is reloaded on every API request.
  * Any part of the application that needs model access imports the singleton
    from app.ai rather than constructing its own instance.

Usage
-----
    # In FastAPI lifespan (main.py):
    from app.ai import model_manager
    await model_manager.initialize()

    # In a route or service:
    from app.ai import model_manager
    result = model_manager.get_symptom_model().infer(symptoms, language)

Design: lazy + silent
---------------------
initialize() attempts to load each model but never raises an exception if
weights are missing.  This ensures the server always starts regardless of
whether trained model artefacts are present.
"""

import logging

from app.ai.symptom_model import DistilBERTSymptomModel
from app.ai.image_model import YOLOv8ImageModel
from app.ai.report_model import T5ReportModel

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Singleton coordinator for all MediQ AI model services.

    Attributes
    ----------
    _symptom_model : DistilBERTSymptomModel
    _skin_model    : YOLOv8ImageModel (skin domain: HAM10000)
    _eye_model     : YOLOv8ImageModel (eye domain: SLID anterior-eye)
    _image_model   : YOLOv8ImageModel (backward compatibility alias)
    _report_model  : T5ReportModel
    _initialised   : bool – True after initialize() has been called
    """

    def __init__(self) -> None:
        self._symptom_model = DistilBERTSymptomModel()
        self._skin_model = YOLOv8ImageModel(domain="skin")
        self._eye_model = YOLOv8ImageModel(domain="eye")
        self._image_model = self._skin_model
        self._report_model = T5ReportModel()
        self._initialised: bool = False

    # ─────────────────────────────────────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────────────────────────────────────

    def initialize(self) -> None:
        """
        Attempt to load all registered AI models.

        Called once during application startup (FastAPI lifespan).
        Safe to call multiple times — subsequent calls are no-ops.

        Behaviour
        ---------
        * For each model, calls model.load() which is itself idempotent.
        * If a model's weights are missing, load() logs an INFO message and
          returns without raising.
        * The server continues to start even if all models are unavailable.
        """
        if self._initialised:
            logger.debug("ModelManager already initialised — skipping.")
            return

        logger.info("ModelManager: initialising AI model services...")

        self._safe_load(self._symptom_model)
        self._safe_load(self._skin_model)
        self._safe_load(self._eye_model)
        self._safe_load(self._report_model)

        self._initialised = True
        logger.info(
            "ModelManager initialised. Status: %s",
            {k: v["available"] for k, v in self.get_status().items()},
        )

    @staticmethod
    def _safe_load(model) -> None:
        """Wrap model.load() to guarantee no uncaught exception reaches startup."""
        try:
            model.load()
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Unexpected error while loading model '%s': %s",
                getattr(model, "_model_name", "unknown"),
                exc,
                exc_info=True,
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Model accessors
    # ─────────────────────────────────────────────────────────────────────────

    def get_symptom_model(self) -> DistilBERTSymptomModel:
        """Return the DistilBERT symptom analysis model service."""
        return self._symptom_model

    def get_skin_model(self) -> YOLOv8ImageModel:
        """Return the YOLOv8 skin lesion detection model service."""
        return self._skin_model

    def get_eye_model(self) -> YOLOv8ImageModel:
        """Return the YOLOv8 anterior-eye pathology detection model service."""
        return self._eye_model

    def get_image_model(self, domain: str = "skin") -> YOLOv8ImageModel:
        """
        Return the YOLOv8 medical image detection model service.
        Accepts optional domain ('skin' or 'eye'). Defaults to skin for backward compatibility.
        """
        if domain == "eye":
            return self._eye_model
        return self._skin_model

    def get_report_model(self) -> T5ReportModel:
        """Return the T5-small report summarisation model service."""
        return self._report_model

    # ─────────────────────────────────────────────────────────────────────────
    # Status
    # ─────────────────────────────────────────────────────────────────────────

    def get_status(self) -> dict:
        """
        Aggregate availability status from all registered model services.

        Returns a dictionary safe for inclusion in API responses.
        Filesystem paths are **not** included.

        Returns
        -------
        {
            "symptom_model": {"model_name": str, "available": bool, "loaded": bool},
            "image_model":   {"model_name": str, "available": bool, "loaded": bool},
            "skin_model":    {"model_name": str, "available": bool, "loaded": bool},
            "eye_model":     {"model_name": str, "available": bool, "loaded": bool},
            "report_model":  {"model_name": str, "available": bool, "loaded": bool},
        }
        """
        return {
            "symptom_model": self._symptom_model.status(),
            "image_model": self._image_model.status(),
            "skin_model": self._skin_model.status(),
            "eye_model": self._eye_model.status(),
            "report_model": self._report_model.status(),
        }

    @property
    def is_initialised(self) -> bool:
        """True after initialize() has been called at least once."""
        return self._initialised
