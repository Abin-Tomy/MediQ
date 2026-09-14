"""
Health Record Management Service.

Encapsulates Firestore persistence, retrieval, and deletion of patient health records.
Strictly guarantees patient ownership and isolation derived from authenticated JWT credentials.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from google.cloud.firestore_v1.base_query import FieldFilter

from app.database import db
from app.models.record import RecordCreateRequest, RecordResponse

logger = logging.getLogger(__name__)


async def create_record(
    patient_uid: str,
    data: RecordCreateRequest,
) -> RecordResponse:
    """
    Create and persist a new health record document for the authenticated patient.
    """
    # Verify patient profile
    try:
        user_doc = db.collection("users").document(patient_uid).get()
        if not user_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient profile not found.",
            )
        if not user_doc.to_dict().get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Patient account is deactivated.",
            )

        now = datetime.now(timezone.utc).isoformat()
        doc_ref = db.collection("health_records").document()
        record_id = doc_ref.id

        record_data = {
            "id": record_id,
            "patient_uid": patient_uid,
            "record_type": data.record_type,
            "title": data.title,
            "description": data.description,
            "record_date": data.record_date,
            "file_name": data.file_name,
            "file_url": data.file_url,
            "storage_path": data.storage_path,
            "file_type": data.file_type,
            "file_size": data.file_size,
            "doctor_uid": data.doctor_uid,
            "doctor_name": data.doctor_name,
            "notes": data.notes,
            "created_at": now,
            "updated_at": now,
        }

        # Store in Firestore
        doc_ref.set(record_data)
        return RecordResponse(**record_data)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error creating health record in Firestore: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create health record. Please try again later.",
        )


async def get_patient_records(
    patient_uid: str,
    record_type: Optional[str] = None,
) -> list[RecordResponse]:
    """
    Retrieve all health records belonging to the authenticated patient.
    Optionally filters by record_type and returns records ordered chronologically
    with the newest record_date and creation time first.
    """
    try:
        query = db.collection("health_records").where(
            filter=FieldFilter("patient_uid", "==", patient_uid)
        )
        docs = query.stream()

        records: list[RecordResponse] = []
        for doc in docs:
            d = doc.to_dict()
            if record_type and d.get("record_type") != record_type:
                continue
            records.append(RecordResponse(**d))

        # Consistent sort: newest record_date first, then newest created_at first
        records.sort(
            key=lambda r: (r.record_date, r.created_at),
            reverse=True,
        )
        return records

    except Exception as exc:
        logger.error(f"Error fetching health records from Firestore: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve health records. Please try again later.",
        )


async def delete_record(
    record_id: str,
    patient_uid: str,
) -> dict[str, str]:
    """
    Delete a health record document after strictly verifying that the authenticated
    user is the owner of the record.
    """
    try:
        doc_ref = db.collection("health_records").document(record_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health record not found.",
            )

        rec = doc.to_dict()

        # Authorization: must match record owner
        if rec.get("patient_uid") != patient_uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this health record.",
            )

        doc_ref.delete()
        return {
            "status": "success",
            "message": "Health record deleted successfully.",
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error deleting health record from Firestore: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete health record. Please try again later.",
        )
