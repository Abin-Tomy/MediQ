"""
Doctor Discovery and Management API Routes.

Exposes endpoints for:
- GET /doctors: Search and filter approved doctors by specialization or location.
- GET /doctors/me: Retrieve authenticated doctor's full professional profile.
- PATCH /doctors/me: Update authenticated doctor's professional fields (fee, availability, bio).
- GET /doctors/{id}: Retrieve public profile for a specific approved doctor.

Route order note: /me routes are declared before /{id} to prevent path parameter shadowing.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.doctor import (
    DoctorProfileUpdate,
    DoctorPublicResponse,
    DoctorSelfProfileResponse,
)
from app.services.doctor_service import (
    get_approved_doctor,
    get_doctor_self_profile,
    list_approved_doctors,
    update_doctor_profile,
)
from app.utils.auth_dependencies import get_current_user

router = APIRouter(tags=["Doctors"])


@router.get(
    "",
    response_model=list[DoctorPublicResponse],
    status_code=status.HTTP_200_OK,
    summary="Discover approved doctors",
    description=(
        "Retrieve all verified, active doctors available for consultation bookings. "
        "Supports optional filtering by clinical specialization or geographic location."
    ),
)
async def get_doctors(
    specialization: Optional[str] = Query(
        default=None,
        description="Filter by medical specialty (e.g., 'Cardiologist', 'Dermatologist', 'General Physician')",
    ),
    location: Optional[str] = Query(
        default=None,
        description="Filter by practice location or city",
    ),
    _: dict = Depends(get_current_user),
) -> list[DoctorPublicResponse]:
    """
    Search approved doctors with optional query filters.
    """
    return await list_approved_doctors(specialization=specialization, location=location)


@router.get(
    "/me",
    response_model=DoctorSelfProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get doctor self-profile",
    description=(
        "Retrieve full professional profile for the authenticated doctor. "
        "Doctor UID is derived strictly from the authenticated JWT token."
    ),
)
async def get_doctor_me(
    current_user: dict = Depends(get_current_user),
) -> DoctorSelfProfileResponse:
    """
    Fetch the authenticated doctor's full professional profile.
    """
    role = current_user.get("role")
    if role not in ("doctor", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor access required.",
        )

    doctor_uid = current_user.get("uid")
    return await get_doctor_self_profile(doctor_uid=doctor_uid)


@router.patch(
    "/me",
    response_model=DoctorSelfProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update doctor self-profile",
    description=(
        "Update professional information (consultation fee, availability, bio, specialization, location). "
        "Restricted to approved doctors. Disallows unauthorized self-approval or security field tampering."
    ),
)
async def patch_doctor_me(
    update_data: DoctorProfileUpdate,
    current_user: dict = Depends(get_current_user),
) -> DoctorSelfProfileResponse:
    """
    Perform a partial update on the authenticated doctor's professional profile.
    """
    role = current_user.get("role")
    if role not in ("doctor", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor access required.",
        )

    doctor_uid = current_user.get("uid")
    return await update_doctor_profile(doctor_uid=doctor_uid, update_data=update_data)


@router.get(
    "/{id}",
    response_model=DoctorPublicResponse,
    status_code=status.HTTP_200_OK,
    summary="Get approved doctor profile",
    description=(
        "Retrieve the public profile, consultation fee, and scheduling availability "
        "for a single approved doctor. Returns 404 if the doctor does not exist or is not approved."
    ),
)
async def get_doctor_by_id(
    id: str,
    _: dict = Depends(get_current_user),
) -> DoctorPublicResponse:
    """
    Fetch public details of a specific approved doctor.
    """
    return await get_approved_doctor(doctor_uid=id)
