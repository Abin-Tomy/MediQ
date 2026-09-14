"""
Medication API Routes.

Exposes endpoints for patient medication regimen tracking:
- POST /medications: Log a new prescribed or over-the-counter medication.
- GET /medications/mine: Retrieve medications belonging to the authenticated patient.
- PUT /medications/{medication_id}: Update an existing medication record.
- DELETE /medications/{medication_id}: Remove a medication record.

All endpoints strictly enforce JWT Bearer authentication and patient record ownership.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.medication import (
    MedicationCreateRequest,
    MedicationResponse,
    MedicationUpdateRequest,
)
from app.services.medication_service import (
    create_medication,
    delete_medication,
    get_patient_medications,
    update_medication,
)
from app.utils.auth_dependencies import get_current_user

router = APIRouter(tags=["Medications"])


@router.post(
    "",
    response_model=MedicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a medication record",
    description=(
        "Log a new medication entry for the authenticated patient. "
        "Patient identity is established directly from the authenticated JWT token."
    ),
)
async def create_medication_endpoint(
    data: MedicationCreateRequest,
    current_user: dict = Depends(get_current_user),
) -> MedicationResponse:
    """
    Log a medication record for the current patient.
    """
    role = current_user.get("role")
    if role == "pending":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accounts awaiting verification cannot manage medications.",
        )

    patient_uid = current_user.get("uid")
    return await create_medication(patient_uid=patient_uid, data=data)


@router.get(
    "/mine",
    response_model=list[MedicationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get patient's medications",
    description="Retrieve all medication records belonging to the authenticated patient.",
)
async def get_my_medications(
    active_only: Optional[bool] = Query(
        default=None,
        description="Filter for only active (true) or inactive (false) medications",
    ),
    current_user: dict = Depends(get_current_user),
) -> list[MedicationResponse]:
    """
    Retrieve medication history and active prescriptions for the authenticated patient.
    """
    patient_uid = current_user.get("uid")
    return await get_patient_medications(patient_uid=patient_uid, active_only=active_only)


@router.put(
    "/{medication_id}",
    response_model=MedicationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a medication record",
    description=(
        "Update details of an existing medication record. "
        "Restricted to the patient who owns the record."
    ),
)
async def update_medication_endpoint(
    medication_id: str,
    data: MedicationUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> MedicationResponse:
    """
    Modify an existing medication record owned by the authenticated patient.
    """
    patient_uid = current_user.get("uid")
    return await update_medication(
        medication_id=medication_id,
        patient_uid=patient_uid,
        data=data,
    )


@router.delete(
    "/{medication_id}",
    response_model=dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Delete a medication record",
    description=(
        "Permanently delete a medication record. "
        "Restricted to the patient who owns the record."
    ),
)
async def delete_medication_endpoint(
    medication_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict[str, str]:
    """
    Delete a medication record owned by the authenticated patient.
    """
    patient_uid = current_user.get("uid")
    return await delete_medication(
        medication_id=medication_id,
        patient_uid=patient_uid,
    )
