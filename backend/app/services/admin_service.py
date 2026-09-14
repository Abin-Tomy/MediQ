"""
Admin Service Module.

Provides all business logic for admin user management operations:
- List and search all users (filterable by role)
- Retrieve a single user's full profile
- Update a user's role or active status
- Soft-delete (deactivate) users
- List all pending doctor applications
- Approve or reject pending doctor applications
- Manually add a new doctor account (immediately approved)
"""

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, status
from firebase_admin import auth as firebase_auth

from app.database import db
from app.models.user import (
    AdminAddDoctor,
    AdminUpdateUser,
    DoctorProfileResponse,
    UserProfileResponse,
)
from app.services.auth_service import _fetch_user_profile, _trigger_firebase_password_reset_email


# ─────────────────────────────────────────────────────────────────────────────
# List All Users
# ─────────────────────────────────────────────────────────────────────────────

async def list_users(role_filter: Optional[str] = None) -> list[UserProfileResponse]:
    """
    Return all users in the system, optionally filtered by role.

    Supported role values: patient, pending, doctor, admin.
    Doctor-specific data is not merged here to keep list responses lightweight.
    """
    query = db.collection("users")

    if role_filter:
        from google.cloud.firestore_v1.base_query import FieldFilter
        query = query.where(filter=FieldFilter("role", "==", role_filter))

    docs = query.stream()

    users = []
    for doc in docs:
        data = doc.to_dict()
        users.append(UserProfileResponse(
            uid=data["uid"],
            name=data["name"],
            email=data["email"],
            role=data["role"],
            phone_number=data.get("phone_number"),
            profile_picture_url=data.get("profile_picture_url"),
            is_email_verified=data.get("is_email_verified", False),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at"),
            doctor_profile=None,   # Omitted in list view for performance
        ))

    return users


# ─────────────────────────────────────────────────────────────────────────────
# Get Single User
# ─────────────────────────────────────────────────────────────────────────────

async def get_user(uid: str) -> UserProfileResponse:
    """
    Retrieve the full profile of a specific user including doctor details if applicable.
    """
    return _fetch_user_profile(uid)


# ─────────────────────────────────────────────────────────────────────────────
# Update User (role / active status)
# ─────────────────────────────────────────────────────────────────────────────

async def update_user(uid: str, data: AdminUpdateUser) -> UserProfileResponse:
    """
    Allow an admin to update a user's role and/or active status.

    Role changes take effect immediately — the user's next login or token
    refresh will return a JWT reflecting the new role.
    """
    user_doc = db.collection("users").document(uid).get()
    if not user_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    updates: dict[str, Any] = {}
    if data.role is not None:
        updates["role"] = data.role.value
    if data.is_active is not None:
        updates["is_active"] = data.is_active
        # Mirror active status in Firebase Auth
        try:
            firebase_auth.update_user(uid, disabled=not data.is_active)
        except Exception as e:
            print(f"[admin_service] Firebase Auth update_user notice: {e}")

    if updates:
        db.collection("users").document(uid).update(updates)

    return _fetch_user_profile(uid)


# ─────────────────────────────────────────────────────────────────────────────
# Deactivate (Soft Delete) User
# ─────────────────────────────────────────────────────────────────────────────

async def deactivate_user(uid: str) -> dict[str, str]:
    """
    Soft-delete a user by setting is_active=False and disabling their Firebase Auth account.
    Data is preserved in Firestore for audit purposes.
    """
    user_doc = db.collection("users").document(uid).get()
    if not user_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    db.collection("users").document(uid).update({"is_active": False})

    try:
        firebase_auth.update_user(uid, disabled=True)
    except Exception as e:
        print(f"[admin_service] Firebase Auth disable notice: {e}")

    return {"message": "User deactivated successfully."}


# ─────────────────────────────────────────────────────────────────────────────
# List Pending Doctors
# ─────────────────────────────────────────────────────────────────────────────

async def list_pending_doctors() -> list[UserProfileResponse]:
    """
    Return all users with role='pending' along with their doctor profile data
    (license document URL and submitted credentials) for admin review.
    """
    from google.cloud.firestore_v1.base_query import FieldFilter

    docs = (
        db.collection("users")
        .where(filter=FieldFilter("role", "==", "pending"))
        .stream()
    )

    results = []
    for doc in docs:
        data = doc.to_dict()
        uid = data["uid"]

        # Fetch associated doctor document for license/specialization review
        doctor_doc = db.collection("doctors").document(uid).get()
        doctor_profile = None
        if doctor_doc.exists:
            d = doctor_doc.to_dict()
            doctor_profile = DoctorProfileResponse(
                specialization=d.get("specialization"),
                location=d.get("location"),
                available_slots=d.get("available_slots", []),
                rating=d.get("rating"),
                is_approved=d.get("is_approved", False),
                license_document_url=d.get("license_document_url"),
            )

        results.append(UserProfileResponse(
            uid=uid,
            name=data["name"],
            email=data["email"],
            role=data["role"],
            phone_number=data.get("phone_number"),
            profile_picture_url=data.get("profile_picture_url"),
            is_email_verified=data.get("is_email_verified", False),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at"),
            doctor_profile=doctor_profile,
        ))

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Approve Pending Doctor
# ─────────────────────────────────────────────────────────────────────────────

async def approve_doctor(uid: str) -> dict[str, str]:
    """
    Approve a pending doctor application.

    Updates the user's role from 'pending' to 'doctor' in the users collection
    and marks is_approved=True in the doctors collection.
    The next time the doctor refreshes their token or logs in, their JWT will
    reflect the new 'doctor' role.
    """
    user_doc = db.collection("users").document(uid).get()
    if not user_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if user_doc.to_dict().get("role") != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not in pending status.",
        )

    db.collection("users").document(uid).update({"role": "doctor"})
    db.collection("doctors").document(uid).update({"is_approved": True})

    return {"message": "Doctor approved successfully. They can now access doctor features."}


# ─────────────────────────────────────────────────────────────────────────────
# Reject Pending Doctor
# ─────────────────────────────────────────────────────────────────────────────

async def reject_doctor(uid: str) -> dict[str, str]:
    """
    Reject a pending doctor application.

    Reverts the user's role back to 'patient' so they can still use the app
    as a regular patient. Sets is_approved=False in the doctors collection.
    """
    user_doc = db.collection("users").document(uid).get()
    if not user_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if user_doc.to_dict().get("role") != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not in pending status.",
        )

    db.collection("users").document(uid).update({"role": "patient"})
    db.collection("doctors").document(uid).update({"is_approved": False})

    return {"message": "Doctor application rejected. User role reverted to patient."}


# ─────────────────────────────────────────────────────────────────────────────
# Admin Manually Adds a Doctor
# ─────────────────────────────────────────────────────────────────────────────

async def admin_add_doctor(data: AdminAddDoctor) -> dict[str, str]:
    """
    Admin directly creates a verified doctor account without the pending flow.

    1. Creates a Firebase Auth user without a password.
    2. Creates users/{uid} with role='doctor' immediately.
    3. Creates doctors/{uid} with is_approved=True.
    4. Triggers a Firebase password-reset email so the doctor sets their own password.

    This bypasses the pending approval stage entirely — use for trusted additions.
    """
    from google.cloud.firestore_v1.base_query import FieldFilter

    # Prevent duplicate email
    existing = (
        db.collection("users")
        .where(filter=FieldFilter("email", "==", data.email))
        .limit(1)
        .get()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # Create Firebase Auth entry without a password — the reset email will prompt them
    try:
        firebase_user = firebase_auth.create_user(
            email=data.email,
            display_name=data.name,
            email_verified=False,
        )
    except firebase_auth.EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Firebase user creation failed: {str(e)}",
        )

    uid = firebase_user.uid
    now = datetime.now(timezone.utc).isoformat()

    # Create the user document — password is managed entirely by Firebase Auth
    db.collection("users").document(uid).set({
        "uid": uid,
        "name": data.name,
        "email": data.email,
        "phone_number": data.phone_number,
        "role": "doctor",
        "profile_picture_url": None,
        "is_email_verified": False,
        "is_active": True,
        "created_at": now,
    })

    # Create the doctors document as fully approved
    db.collection("doctors").document(uid).set({
        "specialization": data.specialization,
        "location": data.location,
        "license_document_url": None,   # Admin-added doctors skip document upload
        "available_slots": [],
        "rating": None,
        "is_approved": True,
        "created_at": now,
    })

    # Send a Firebase password-reset email so the doctor can set their credentials
    try:
        reset_link = firebase_auth.generate_password_reset_link(data.email)
        _trigger_firebase_password_reset_email(data.email, reset_link)
    except Exception as e:
        print(f"[admin_service] Password reset email notice: {e}")

    return {
        "message": f"Doctor account created for {data.email}. A password setup email has been sent.",
        "uid": uid,
    }
