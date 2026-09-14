"""
Medication Management Service.

Handles persistence, retrieval, modification, and deletion of patient medications.
Enforces participant ownership strictly through the authenticated JWT identity.
"""

from datetime import date, datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from google.cloud.firestore_v1.base_query import FieldFilter

from app.database import db
from app.models.medication import (
    MedicationCreateRequest,
    MedicationResponse,
    MedicationUpdateRequest,
)


async def create_medication(
    patient_uid: str,
    data: MedicationCreateRequest,
) -> MedicationResponse:
    """
    Create and persist a new medication record for the authenticated patient.
    """
    # Verify patient profile
    patient_doc = db.collection("users").document(patient_uid).get()
    if not patient_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found.",
        )
    if not patient_doc.to_dict().get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patient account is deactivated.",
        )

    # Calculate active status based on end_date
    is_active = True
    if data.end_date:
        try:
            e_date = datetime.strptime(data.end_date, "%Y-%m-%d").date()
            if e_date < date.today():
                is_active = False
        except ValueError:
            pass

    now = datetime.now(timezone.utc).isoformat()
    doc_ref = db.collection("medications").document()
    medication_id = doc_ref.id

    record = {
        "id": medication_id,
        "patient_uid": patient_uid,
        "medication_name": data.medication_name,
        "dosage": data.dosage,
        "frequency": data.frequency,
        "route": data.route or "Oral",
        "start_date": data.start_date,
        "end_date": data.end_date,
        "instructions": data.instructions,
        "prescribing_doctor_uid": data.prescribing_doctor_uid,
        "prescribing_doctor_name": data.prescribing_doctor_name,
        "notes": data.notes,
        "active": is_active,
        "created_at": now,
        "updated_at": now,
    }

    doc_ref.set(record)
    return MedicationResponse(**record)


async def get_patient_medications(
    patient_uid: str,
    active_only: Optional[bool] = None,
) -> list[MedicationResponse]:
    """
    Retrieve all medication records belonging to the authenticated patient.
    Optionally filters for active regimens.
    """
    docs = (
        db.collection("medications")
        .where(filter=FieldFilter("patient_uid", "==", patient_uid))
        .stream()
    )

    results: list[MedicationResponse] = []
    for doc in docs:
        d = doc.to_dict()
        if active_only is not None:
            if active_only and not d.get("active", True):
                continue
            if not active_only and d.get("active", True):
                continue
        results.append(MedicationResponse(**d))

    # Sort newest first (by created_at or updated_at descending)
    results.sort(key=lambda x: x.created_at, reverse=True)
    return results


async def update_medication(
    medication_id: str,
    patient_uid: str,
    data: MedicationUpdateRequest,
) -> MedicationResponse:
    """
    Update an existing medication record.
    Guarantees that only the authenticated owner can modify the record.
    """
    doc_ref = db.collection("medications").document(medication_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found.",
        )

    med = doc.to_dict()

    # Ownership validation
    if med.get("patient_uid") != patient_uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this medication.",
        )

    # Date chronology check between incoming updates and stored values
    effective_start = data.start_date if data.start_date is not None else med.get("start_date")
    effective_end = data.end_date if data.end_date is not None else med.get("end_date")
    if effective_start and effective_end:
        try:
            s_date = datetime.strptime(effective_start, "%Y-%m-%d").date()
            e_date = datetime.strptime(effective_end, "%Y-%m-%d").date()
            if e_date < s_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="end_date cannot be before start_date.",
                )
        except ValueError:
            pass

    # Extract non-None update fields
    update_fields = data.model_dump(exclude_unset=True)

    # Protect immutable ownership & audit fields
    update_fields.pop("id", None)
    update_fields.pop("patient_uid", None)
    update_fields.pop("created_at", None)

    now = datetime.now(timezone.utc).isoformat()
    update_fields["updated_at"] = now

    doc_ref.update(update_fields)
    med.update(update_fields)

    return MedicationResponse(**med)


async def delete_medication(
    medication_id: str,
    patient_uid: str,
) -> dict[str, str]:
    """
    Delete a medication record after verifying owner identity.
    """
    doc_ref = db.collection("medications").document(medication_id)
    doc = doc_ref.get()

    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medication not found.",
        )

    med = doc.to_dict()

    # Ownership validation
    if med.get("patient_uid") != patient_uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this medication.",
        )

    doc_ref.delete()
    return {"message": "Medication deleted successfully."}
