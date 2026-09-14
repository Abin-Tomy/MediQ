"""
Health Record API Routes.

Exposes endpoints for patient medical record management:
- POST /records: Register a new health record metadata entry.
- GET /records/mine: Retrieve medical records belonging to the authenticated patient.
- DELETE /records/{record_id}: Delete a health record owned by the patient.

Strictly enforces JWT Bearer authentication and patient ownership isolation.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.record import RecordCreateRequest, RecordResponse
from app.services.record_service import (
    create_record,
    delete_record,
    get_patient_records,
)
from app.utils.auth_dependencies import get_current_user

router = APIRouter(tags=["Health Records"])


@router.post(
    "",
    response_model=RecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a health record",
    description=(
        "Register a new medical record metadata entry for the authenticated patient. "
        "Patient identity is established strictly from the verified JWT token."
    ),
)
async def create_record_endpoint(
    data: RecordCreateRequest,
    current_user: dict = Depends(get_current_user),
) -> RecordResponse:
    """
    Log a health record metadata reference for the current patient.
    """
    role = current_user.get("role")
    if role == "pending":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accounts awaiting verification cannot manage health records.",
        )

    patient_uid = current_user.get("uid")
    return await create_record(patient_uid=patient_uid, data=data)


@router.get(
    "/mine",
    response_model=list[RecordResponse],
    status_code=status.HTTP_200_OK,
    summary="Get patient's health records",
    description="Retrieve all medical records belonging to the authenticated patient, sorted newest first.",
)
async def get_my_records(
    record_type: Optional[str] = Query(
        default=None,
        description="Filter records by category (e.g., blood_report, prescription, scan_report)",
    ),
    current_user: dict = Depends(get_current_user),
) -> list[RecordResponse]:
    """
    Retrieve medical record history for the authenticated patient.
    """
    patient_uid = current_user.get("uid")
    return await get_patient_records(patient_uid=patient_uid, record_type=record_type)


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a health record",
    description=(
        "Delete a health record document. Restricted strictly to the patient who owns the record."
    ),
)
async def delete_record_endpoint(
    record_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict[str, str]:
    """
    Remove a health record metadata document owned by the authenticated patient.
    """
    patient_uid = current_user.get("uid")
    return await delete_record(record_id=record_id, patient_uid=patient_uid)
