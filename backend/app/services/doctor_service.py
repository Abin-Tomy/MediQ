"""
Doctor Discovery and Management Service.

Handles:
- Discovering approved doctors (with optional specialization/location filters)
- Fetching individual approved doctor public profiles
- Retrieving authenticated doctor's full professional profile (GET /doctors/me)
- Secure partial updates of doctor professional profile (PATCH /doctors/me)
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from google.cloud.firestore_v1.base_query import FieldFilter

from app.database import db
from app.models.doctor import (
    DoctorProfileUpdate,
    DoctorPublicResponse,
    DoctorSelfProfileResponse,
)


async def list_approved_doctors(
    specialization: Optional[str] = None,
    location: Optional[str] = None,
) -> list[DoctorPublicResponse]:
    """
    Retrieve all verified and approved doctors for patient booking.
    Optionally filters by clinical specialization or practice location.
    """
    doctor_docs = (
        db.collection("doctors")
        .where(filter=FieldFilter("is_approved", "==", True))
        .stream()
    )

    results: list[DoctorPublicResponse] = []

    for doc in doctor_docs:
        doc_data = doc.to_dict()
        uid = doc.id

        user_doc = db.collection("users").document(uid).get()
        if not user_doc.exists:
            continue

        user_data = user_doc.to_dict()
        if not user_data.get("is_active", True) or user_data.get("role") != "doctor":
            continue

        doc_specialization = doc_data.get("specialization") or "General Medicine"
        doc_location = doc_data.get("location") or "Kerala"

        if specialization and specialization.strip().lower() not in doc_specialization.lower():
            continue

        if location and location.strip().lower() not in doc_location.lower():
            continue

        results.append(
            DoctorPublicResponse(
                uid=uid,
                name=user_data.get("name", "Doctor"),
                specialization=doc_specialization,
                location=doc_location,
                consultation_fee=doc_data.get("consultation_fee"),
                bio=doc_data.get("bio"),
                rating=doc_data.get("rating"),
                review_count=doc_data.get("review_count", 0),
                available_days=doc_data.get("available_days")
                or ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                available_hours=doc_data.get("available_hours")
                or {"start": "09:00", "end": "17:00"},
                profile_picture_url=user_data.get("profile_picture_url"),
            )
        )

    return results


async def get_approved_doctor(doctor_uid: str) -> DoctorPublicResponse:
    """
    Retrieve public profile for a single approved doctor by UID.
    Returns 404 if the doctor is not found, not approved, or deactivated.
    """
    doc_ref = db.collection("doctors").document(doctor_uid).get()
    if not doc_ref.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found.",
        )

    doc_data = doc_ref.to_dict()
    if not doc_data.get("is_approved", False):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor is not approved or currently unavailable.",
        )

    user_ref = db.collection("users").document(doctor_uid).get()
    if not user_ref.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile is incomplete.",
        )

    user_data = user_ref.to_dict()
    if not user_data.get("is_active", True) or user_data.get("role") != "doctor":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor account is currently inactive.",
        )

    return DoctorPublicResponse(
        uid=doctor_uid,
        name=user_data.get("name", "Doctor"),
        specialization=doc_data.get("specialization") or "General Medicine",
        location=doc_data.get("location") or "Kerala",
        consultation_fee=doc_data.get("consultation_fee"),
        bio=doc_data.get("bio"),
        rating=doc_data.get("rating"),
        review_count=doc_data.get("review_count", 0),
        available_days=doc_data.get("available_days")
        or ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        available_hours=doc_data.get("available_hours")
        or {"start": "09:00", "end": "17:00"},
        profile_picture_url=user_data.get("profile_picture_url"),
    )


async def get_doctor_self_profile(doctor_uid: str) -> DoctorSelfProfileResponse:
    """
    Retrieve full professional profile for an authenticated doctor.
    """
    doc_ref = db.collection("doctors").document(doctor_uid).get()
    user_ref = db.collection("users").document(doctor_uid).get()

    if not doc_ref.exists or not user_ref.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found.",
        )

    doc_data = doc_ref.to_dict()
    user_data = user_ref.to_dict()

    return DoctorSelfProfileResponse(
        uid=doctor_uid,
        name=user_data.get("name", "Doctor"),
        email=user_data.get("email", ""),
        specialization=doc_data.get("specialization") or "General Medicine",
        location=doc_data.get("location") or "Kerala",
        consultation_fee=doc_data.get("consultation_fee"),
        bio=doc_data.get("bio"),
        rating=doc_data.get("rating"),
        review_count=doc_data.get("review_count", 0),
        available_days=doc_data.get("available_days")
        or ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        available_hours=doc_data.get("available_hours")
        or {"start": "09:00", "end": "17:00"},
        profile_picture_url=user_data.get("profile_picture_url"),
        is_approved=doc_data.get("is_approved", False),
    )


async def update_doctor_profile(
    doctor_uid: str,
    update_data: DoctorProfileUpdate,
) -> DoctorSelfProfileResponse:
    """
    Allow an approved doctor to update their professional details.
    Restricts changes to non-security fields. Prevents self-approval.
    """
    doc_ref = db.collection("doctors").document(doctor_uid).get()
    user_ref = db.collection("users").document(doctor_uid).get()

    if not doc_ref.exists or not user_ref.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found.",
        )

    doc_data = doc_ref.to_dict()
    user_data = user_ref.to_dict()

    if not doc_data.get("is_approved", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only approved doctors can update their professional profile.",
        )

    if not user_data.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor account is deactivated.",
        )

    now = datetime.now(timezone.utc).isoformat()

    # User document updates (name, profile_picture_url)
    user_updates = {}
    if update_data.name is not None:
        user_updates["name"] = update_data.name
    if update_data.profile_picture_url is not None:
        user_updates["profile_picture_url"] = update_data.profile_picture_url

    if user_updates:
        user_updates["updated_at"] = now
        db.collection("users").document(doctor_uid).update(user_updates)
        user_data.update(user_updates)

    # Doctor document updates (specialization, location, fee, bio, available_days, available_hours)
    doc_updates = {}
    if update_data.specialization is not None:
        doc_updates["specialization"] = update_data.specialization
    if update_data.location is not None:
        doc_updates["location"] = update_data.location
    if update_data.consultation_fee is not None:
        doc_updates["consultation_fee"] = update_data.consultation_fee
    if update_data.bio is not None:
        doc_updates["bio"] = update_data.bio
    if update_data.available_days is not None:
        doc_updates["available_days"] = update_data.available_days
    if update_data.available_hours is not None:
        doc_updates["available_hours"] = update_data.available_hours.model_dump()

    if doc_updates:
        doc_updates["updated_at"] = now
        db.collection("doctors").document(doctor_uid).update(doc_updates)
        doc_data.update(doc_updates)

    return DoctorSelfProfileResponse(
        uid=doctor_uid,
        name=user_data.get("name", "Doctor"),
        email=user_data.get("email", ""),
        specialization=doc_data.get("specialization") or "General Medicine",
        location=doc_data.get("location") or "Kerala",
        consultation_fee=doc_data.get("consultation_fee"),
        bio=doc_data.get("bio"),
        rating=doc_data.get("rating"),
        review_count=doc_data.get("review_count", 0),
        available_days=doc_data.get("available_days")
        or ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        available_hours=doc_data.get("available_hours")
        or {"start": "09:00", "end": "17:00"},
        profile_picture_url=user_data.get("profile_picture_url"),
        is_approved=doc_data.get("is_approved", False),
    )
