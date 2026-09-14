"""
Admin API Routes.

All endpoints require a valid JWT with role='admin'.
Provides admin controls for:
- Viewing and managing all users
- Reviewing and approving/rejecting pending doctor applications
- Directly adding verified doctor accounts
"""

from typing import Optional

from fastapi import APIRouter, Depends, status

from app.models.user import AdminAddDoctor, AdminUpdateUser, UserProfileResponse
from app.services.admin_service import (
    admin_add_doctor,
    approve_doctor,
    deactivate_user,
    get_user,
    list_pending_doctors,
    list_users,
    reject_doctor,
    update_user,
)
from app.utils.auth_dependencies import require_admin

router = APIRouter(tags=["Admin"])


# ─────────────────────────────────────────────────────────────────────────────
# User Management
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/users",
    response_model=list[UserProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="List all users",
)
async def list_all_users(
    role: Optional[str] = None,
    _: dict = Depends(require_admin),
):
    """
    Return all registered users.
    Optionally filter by role using the ?role= query parameter.
    Accepted values: patient, pending, doctor, admin.
    """
    return await list_users(role_filter=role)


@router.get(
    "/users/{uid}",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific user's profile",
)
async def get_single_user(uid: str, _: dict = Depends(require_admin)):
    """
    Return the full profile of a specific user by UID,
    including doctor-specific fields if the user is a doctor or pending.
    """
    return await get_user(uid)


@router.patch(
    "/users/{uid}",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a user's role or active status",
)
async def update_user_route(
    uid: str,
    data: AdminUpdateUser,
    _: dict = Depends(require_admin),
):
    """
    Update a user's role and/or is_active flag.
    Role changes are reflected immediately on the user's next login or token refresh.
    Deactivating also disables the account in Firebase Auth.
    """
    return await update_user(uid, data)


@router.delete(
    "/users/{uid}",
    status_code=status.HTTP_200_OK,
    summary="Deactivate a user account",
)
async def deactivate_user_route(uid: str, _: dict = Depends(require_admin)):
    """
    Soft-delete a user by setting is_active=False and disabling their Firebase Auth account.
    The user's data is preserved in Firestore for audit purposes.
    """
    return await deactivate_user(uid)


# ─────────────────────────────────────────────────────────────────────────────
# Doctor Management
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/doctors/pending",
    response_model=list[UserProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="List all pending doctor applications",
)
async def list_pending_doctors_route(_: dict = Depends(require_admin)):
    """
    Return all users with role='pending', including their submitted doctor profile
    (specialization, location, and license document URL for admin review).
    """
    return await list_pending_doctors()


@router.post(
    "/doctors/approve/{uid}",
    status_code=status.HTTP_200_OK,
    summary="Approve a pending doctor application",
)
async def approve_doctor_route(uid: str, _: dict = Depends(require_admin)):
    """
    Approve a pending doctor application.
    Sets role='doctor' in the users collection and is_approved=True in the doctors collection.
    The doctor's next login or token refresh will return a JWT with role='doctor'.
    """
    return await approve_doctor(uid)


@router.post(
    "/doctors/reject/{uid}",
    status_code=status.HTTP_200_OK,
    summary="Reject a pending doctor application",
)
async def reject_doctor_route(uid: str, _: dict = Depends(require_admin)):
    """
    Reject a pending doctor application.
    Reverts the user's role back to 'patient' so they can still use the app.
    """
    return await reject_doctor(uid)


@router.post(
    "/doctors",
    status_code=status.HTTP_201_CREATED,
    summary="Admin manually adds a verified doctor",
)
async def admin_add_doctor_route(
    data: AdminAddDoctor,
    _: dict = Depends(require_admin),
):
    """
    Admin directly creates a doctor account — bypasses the pending review stage.
    Role is immediately set to 'doctor' with is_approved=True.
    Firebase sends the doctor a password-setup email so they can set their own credentials.
    """
    return await admin_add_doctor(data)
