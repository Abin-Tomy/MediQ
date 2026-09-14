"""
AI Status API Routes.

Provides operational visibility into the MediQ AI model layer for
authenticated users and operators.

Endpoints
---------
GET /ai/status
    Returns the availability and load status of each AI model service.
    Requires a valid JWT Bearer token.
    Does NOT expose filesystem paths or internal configuration.
"""

import logging
from fastapi import APIRouter, Depends, status

from app.ai import model_manager
from app.utils.auth_dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Status"])


@router.get(
    "/status",
    status_code=status.HTTP_200_OK,
    summary="AI model availability status",
    description=(
        "Returns the load and availability status of each MediQ AI model "
        "(DistilBERT symptom, YOLOv8 image, T5 report). "
        "Requires JWT authentication. Does not expose model file paths."
    ),
)
def get_ai_status(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Endpoint: GET /ai/status

    Requires an authenticated user (any role).

    Response shape
    --------------
    {
        "manager_initialised": bool,
        "models": {
            "symptom_model": {"model_name": str, "available": bool, "loaded": bool},
            "image_model":   {"model_name": str, "available": bool, "loaded": bool},
            "report_model":  {"model_name": str, "available": bool, "loaded": bool},
        }
    }
    """
    return {
        "manager_initialised": model_manager.is_initialised,
        "models": model_manager.get_status(),
    }
