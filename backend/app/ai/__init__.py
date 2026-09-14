"""
MediQ AI Inference Package.

Provides the production-ready AI model architecture for:
- DistilBERT symptom analysis  (app.ai.symptom_model)
- YOLOv8 medical image analysis (app.ai.image_model)
- T5-small report summarisation (app.ai.report_model)

The ModelManager singleton (model_manager) is the sole entry point
for the FastAPI layer.  Import it as::

    from app.ai import model_manager

No route or service should instantiate model classes directly.
"""

from app.ai.model_manager import ModelManager

# Module-level singleton used across the application
model_manager: ModelManager = ModelManager()

__all__ = ["model_manager"]
