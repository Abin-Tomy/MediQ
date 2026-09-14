"""
Analysis API Routes.

Exposes endpoints for AI-powered and rule-based diagnostic analysis:
- POST /analyse/symptoms: Analyzes patient symptoms and provides condition predictions,
  urgency assessment, and specialist recommendation.

Protected by JWT authentication via `get_current_user`.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.models.analysis import (
    FusionInput,
    FusionResponse,
    SymptomAnalysisResponse,
    SymptomInput,
)
from app.services.fusion_service import fuse_modalities
from app.services.symptom_service import analyze_symptoms
from app.utils.auth_dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Analysis"])


@router.post(
    "/symptoms",
    response_model=SymptomAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze patient symptoms",
    description=(
        "Analyzes patient-reported symptoms using deterministic rule-based evaluation "
        "(placeholder for fine-tuned DistilBERT inference). Returns ranked potential conditions, "
        "confidence indicators, triage urgency, and recommended specialist consultation."
    ),
)
async def analyse_symptoms_endpoint(
    request: SymptomInput,
    current_user: dict = Depends(get_current_user),
) -> SymptomAnalysisResponse:
    """
    Endpoint: POST /analyse/symptoms

    Requires an authenticated user (patient, doctor, or admin).
    Accepts natural-language symptom text and returns structured clinical decision support.
    """
    # Enforce role authorization if specified in token
    role = current_user.get("role")
    if role and role not in ("patient", "doctor", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active user access required for symptom analysis.",
        )

    try:
        response = await analyze_symptoms(request)
        return response
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error during symptom analysis: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while analyzing symptoms. Please try again later.",
        )


@router.post(
    "/fuse",
    response_model=FusionResponse,
    status_code=status.HTTP_200_OK,
    summary="Multimodal AI diagnostic fusion",
    description=(
        "Synthesizes clinical evidence across four distinct modalities: patient symptoms (DistilBERT), "
        "skin lesion images (HAM10000 YOLOv8), anterior-eye slit-lamp images (SLID YOLOv8), and medical "
        "reports (T5-small). Dynamically determines active modalities across all 15 non-empty combinations, "
        "enforces strict model execution rules, preserves distinct multi-domain findings, rewards "
        "independent cross-modal corroboration, handles unavailable models safely without fabricating predictions, "
        "and computes conservative clinical urgency with deterministic specialist recommendations."
    ),
)
async def analyse_fuse_endpoint(
    request: FusionInput,
    current_user: dict = Depends(get_current_user),
) -> FusionResponse:
    """
    Endpoint: POST /analyse/fuse

    Requires an authenticated user (patient, doctor, or admin).
    Accepts multimodal inputs (symptoms, skin_image, eye_image, report_text) and returns
    unified clinical decision support.
    """
    role = current_user.get("role")
    if role and role not in ("patient", "doctor", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active user access required for multimodal analysis.",
        )

    try:
        response = await fuse_modalities(request)
        return response
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected error during multimodal fusion: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during multimodal analysis. Please try again later.",
        )

