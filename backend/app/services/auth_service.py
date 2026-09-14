"""
Authentication Service Module.

Handles core business logic for user authentication and profile management:
- Patient registration
- Doctor registration (role = 'pending', creates linked doctors/ document)
- Google OAuth login (auto-creates patient account on first sign-in)
- Email/password login for all roles
- JWT access token refresh
- Current user profile retrieval and editing
- Firebase password reset email trigger
- Legacy OTP verification and password reset (deprecated, kept for compatibility)
"""

import json
import os
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

from fastapi import HTTPException, status
from firebase_admin import auth as firebase_auth
from google.cloud.firestore_v1.base_query import FieldFilter

from app.database import db
from app.models.user import (
    DoctorProfileResponse,
    DoctorRegister,
    GoogleAuthRequest,
    PatientRegister,
    ResetPassword,
    TokenResponse,
    UpdateProfile,
    UserLogin,
    UserProfileResponse,
    VerifyOTP,
)
from app.utils.jwt_handler import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    verify_token,
)
from app.utils.otp_handler import delete_otp, verify_otp as check_otp

# Firebase Web API Key — required for client-side auth operations (password sign-in)
# Set in .env as FIREBASE_WEB_API_KEY
_FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY", "")


# ─────────────────────────────────────────────────────────────────────────────
# Internal Helper: Fetch user + optional doctor profile from Firestore
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_user_profile(uid: str) -> UserProfileResponse:
    """
    Retrieve the full user profile from Firestore.
    If the user is a doctor, also fetches the linked doctors/{uid} document
    and attaches it as doctor_profile.
    """
    user_doc = db.collection("users").document(uid).get()
    if not user_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    data = user_doc.to_dict()
    doctor_profile = None

    # Attach doctor-specific data for approved and pending doctors
    if data.get("role") in ("doctor", "pending"):
        doc_ref = db.collection("doctors").document(uid).get()
        if doc_ref.exists:
            d = doc_ref.to_dict()
            doctor_profile = DoctorProfileResponse(
                specialization=d.get("specialization"),
                location=d.get("location"),
                available_slots=d.get("available_slots", []),
                rating=d.get("rating"),
                is_approved=d.get("is_approved", False),
                license_document_url=d.get("license_document_url"),
            )

    return UserProfileResponse(
        uid=data["uid"],
        name=data["name"],
        email=data["email"],
        role=data["role"],
        phone_number=data.get("phone_number"),
        profile_picture_url=data.get("profile_picture_url"),
        is_email_verified=data.get("is_email_verified", False),
        is_active=data.get("is_active", True),
        created_at=data.get("created_at"),
        doctor_profile=doctor_profile,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Internal Helper: Trigger Firebase Password Reset Email
# ─────────────────────────────────────────────────────────────────────────────

def _trigger_firebase_password_reset_email(email: str, reset_link: Optional[str] = None) -> None:
    """
    Dispatch Firebase's built-in password reset email to the user's inbox.

    Firebase Admin SDK's generate_password_reset_link returns the action URL
    instead of emailing the user. To trigger the actual email delivery, this
    helper posts to Firebase Identity Toolkit's /accounts:sendOobCode endpoint.
    Falls back to the public REST API using the API key embedded in the reset link.
    """
    # Primary: use Firebase Admin SDK's internal HTTP client
    try:
        client = firebase_auth._get_client(None)
        client._user_manager._make_request(
            "post",
            "/accounts:sendOobCode",
            json={"requestType": "PASSWORD_RESET", "email": email},
        )
        return
    except Exception as err:
        print(f"[auth_service] Admin client sendOobCode notice: {err}")

    # Fallback: public Identity Toolkit REST API using the API key from the reset link
    if reset_link:
        try:
            parsed = urlparse(reset_link)
            query_params = parse_qs(parsed.query)
            api_key = query_params.get("apiKey", [None])[0]
            if api_key:
                url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={api_key}"
                payload = json.dumps({"requestType": "PASSWORD_RESET", "email": email}).encode("utf-8")
                req = Request(url, data=payload, headers={"Content-Type": "application/json"})
                with urlopen(req) as resp:
                    resp.read()
        except Exception as err:
            print(f"[auth_service] REST sendOobCode fallback notice: {err}")


# ─────────────────────────────────────────────────────────────────────────────
# Internal Helper: Verify Password via Firebase Auth REST API
# ─────────────────────────────────────────────────────────────────────────────

def _verify_firebase_password(email: str, password: str) -> None:
    """
    Verify an email/password pair against Firebase Authentication.

    Calls the Firebase Identity Toolkit signInWithPassword REST endpoint.
    This is the correct way to validate credentials — Firebase Auth is the
    source of truth, not a locally stored bcrypt hash.

    Raises HTTP 401 if credentials are invalid.
    Raises HTTP 500 if the API key is not configured or Firebase is unreachable.
    """
    if not _FIREBASE_WEB_API_KEY or _FIREBASE_WEB_API_KEY == "your-web-api-key-here":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="FIREBASE_WEB_API_KEY is not configured in .env.",
        )

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={_FIREBASE_WEB_API_KEY}"
    payload = json.dumps({
        "email": email,
        "password": password,
        "returnSecureToken": True,
    }).encode("utf-8")
    req = Request(url, data=payload, headers={"Content-Type": "application/json"})

    try:
        with urlopen(req) as resp:
            resp.read()   # Success — credentials are valid
    except HTTPError as e:
        error_body = json.loads(e.read().decode("utf-8"))
        firebase_error = error_body.get("error", {}).get("message", "UNKNOWN")
        # Map Firebase error codes to clean HTTP responses
        if firebase_error in ("INVALID_PASSWORD", "EMAIL_NOT_FOUND", "INVALID_LOGIN_CREDENTIALS"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )
        if firebase_error == "USER_DISABLED":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Contact support.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Firebase Auth error: {firebase_error}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Firebase Auth unreachable: {str(e)}",
        )


# ─────────────────────────────────────────────────────────────────────────────
# Patient Registration
# ─────────────────────────────────────────────────────────────────────────────

async def register_patient(data: PatientRegister) -> TokenResponse:
    """
    Register a new patient account.

    1. Checks Firestore for duplicate email.
    2. Creates a Firebase Auth user.
    3. Persists the user profile in Firestore with role='patient'.
    4. Returns a JWT access and refresh token pair.
    """
    # Prevent duplicate registrations
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

    # Create the Firebase Auth entry
    try:
        firebase_user = firebase_auth.create_user(
            email=data.email,
            password=data.password,
            display_name=data.name,
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

    # Store user profile in Firestore
    db.collection("users").document(uid).set({
        "uid": uid,
        "name": data.name,
        "email": data.email,
        "phone_number": data.phone_number,
        "role": "patient",
        "profile_picture_url": data.profile_picture_url,
        "is_email_verified": False,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    token_payload: dict[str, Any] = {"uid": uid, "email": data.email, "role": "patient"}
    return TokenResponse(
        access_token=create_access_token(token_payload),
        refresh_token=create_refresh_token(token_payload),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Doctor Registration
# ─────────────────────────────────────────────────────────────────────────────

async def register_doctor(data: DoctorRegister) -> TokenResponse:
    """
    Register a new doctor application.

    1. Checks Firestore for duplicate email.
    2. Creates a Firebase Auth user.
    3. Creates users/{uid} with role='pending'.
    4. Creates doctors/{uid} with specialization, location, and license URL.
    5. Returns a JWT token with role='pending'.
       The Flutter app should restrict access until the admin approves.
    """
    # Prevent duplicate registrations
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

    # Create the Firebase Auth entry
    try:
        firebase_user = firebase_auth.create_user(
            email=data.email,
            password=data.password,
            display_name=data.name,
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

    # Create user profile document
    db.collection("users").document(uid).set({
        "uid": uid,
        "name": data.name,
        "email": data.email,
        "phone_number": data.phone_number,
        "role": "pending",
        "profile_picture_url": data.profile_picture_url,
        "is_email_verified": False,
        "is_active": True,
        "created_at": now,
    })

    # Create doctor-specific document (same uid as key)
    db.collection("doctors").document(uid).set({
        "specialization": data.specialization,
        "location": data.location,
        "license_document_url": data.license_document_url,
        "available_slots": [],
        "rating": None,
        "is_approved": False,
        "created_at": now,
    })

    token_payload: dict[str, Any] = {"uid": uid, "email": data.email, "role": "pending"}
    return TokenResponse(
        access_token=create_access_token(token_payload),
        refresh_token=create_refresh_token(token_payload),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Email / Password Login
# ─────────────────────────────────────────────────────────────────────────────

async def login_user(data: UserLogin) -> TokenResponse:
    """
    Authenticate a user with email and password.

    1. Verifies credentials against Firebase Auth REST API (source of truth).
    2. Fetches the Firestore user document to read the current role and active status.
    3. Returns a JWT pair with the current role embedded — reflects any admin-made
       role changes (e.g., pending → doctor) without requiring re-registration.
    """
    # Step 1: Validate credentials via Firebase Auth.
    # This also handles accounts disabled directly in the Firebase console.
    _verify_firebase_password(data.email, data.password)

    # Step 2: Fetch Firestore profile to get role and active status
    docs = (
        db.collection("users")
        .where(filter=FieldFilter("email", "==", data.email))
        .limit(1)
        .get()
    )
    if not docs:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No profile found for this account. Please register.",
        )

    user_doc = docs[0].to_dict()

    # Block accounts deactivated at the Firestore level
    if not user_doc.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Contact support.",
        )

    token_payload: dict[str, Any] = {
        "uid": user_doc["uid"],
        "email": user_doc["email"],
        "role": user_doc.get("role", "patient"),
    }
    return TokenResponse(
        access_token=create_access_token(token_payload),
        refresh_token=create_refresh_token(token_payload),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Google OAuth Login
# ─────────────────────────────────────────────────────────────────────────────

async def google_login(data: GoogleAuthRequest) -> TokenResponse:
    """
    Authenticate via Google Sign-In using a Firebase ID token.

    The Flutter client performs Google Sign-In via Firebase SDK and receives
    a Firebase ID token. This endpoint verifies that token with Firebase Admin
    SDK, then either:
    - Returns tokens if the user already has a Firestore profile, or
    - Auto-creates a 'patient' profile in Firestore on first sign-in.
    """
    try:
        decoded = firebase_auth.verify_id_token(data.id_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google ID token: {str(e)}",
        )

    uid = decoded["uid"]
    email = decoded.get("email", "")
    name = decoded.get("name", email.split("@")[0])
    picture = decoded.get("picture")

    # Check if user already exists in Firestore
    user_doc = db.collection("users").document(uid).get()

    if not user_doc.exists:
        # First-time Google login — auto-create patient profile
        db.collection("users").document(uid).set({
            "uid": uid,
            "name": name,
            "email": email,
            "phone_number": None,
            "role": "patient",
            "profile_picture_url": picture,
            "is_email_verified": decoded.get("email_verified", False),
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        role = "patient"
    else:
        data_dict = user_doc.to_dict()
        if not data_dict.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Contact support.",
            )
        role = data_dict.get("role", "patient")

    token_payload: dict[str, Any] = {"uid": uid, "email": email, "role": role}
    return TokenResponse(
        access_token=create_access_token(token_payload),
        refresh_token=create_refresh_token(token_payload),
    )


# ─────────────────────────────────────────────────────────────────────────────
# JWT Refresh
# ─────────────────────────────────────────────────────────────────────────────

async def refresh_access_token(refresh_token: str) -> TokenResponse:
    """
    Issue a new access token using a valid refresh token.

    Validates the refresh token's type claim and expiry, then reads the
    current role from Firestore (so the new token reflects any role changes
    made by an admin since the last login).
    """
    payload = verify_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    uid = payload.get("uid")
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed refresh token.",
        )

    # Re-read user from Firestore to pick up any role changes
    user_doc = db.collection("users").document(uid).get()
    if not user_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    data = user_doc.to_dict()
    if not data.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated.",
        )

    token_payload: dict[str, Any] = {
        "uid": uid,
        "email": data["email"],
        "role": data.get("role", "patient"),
    }
    return TokenResponse(
        access_token=create_access_token(token_payload),
        refresh_token=create_refresh_token(token_payload),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Get Current User Profile
# ─────────────────────────────────────────────────────────────────────────────

async def get_me(uid: str) -> UserProfileResponse:
    """
    Return the full profile of the authenticated user.
    For doctors and pending applicants, doctor-specific fields are merged in.
    """
    return _fetch_user_profile(uid)


# ─────────────────────────────────────────────────────────────────────────────
# Update Current User Profile
# ─────────────────────────────────────────────────────────────────────────────

async def update_me(uid: str, role: str, data: UpdateProfile) -> UserProfileResponse:
    """
    Update the authenticated user's own profile.

    - All fields are optional; only provided fields are written.
    - Password change requires current_password (verified via Firebase Auth REST)
      and new_password. Firebase Auth is updated via Admin SDK.
    - Doctors can additionally update specialization and location.
    """
    user_doc = db.collection("users").document(uid).get()
    if not user_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    user_data = user_doc.to_dict()

    # Build user-level update payload
    user_updates: dict[str, Any] = {}
    if data.name is not None:
        user_updates["name"] = data.name.strip()
    if data.phone_number is not None:
        user_updates["phone_number"] = data.phone_number
    if data.profile_picture_url is not None:
        user_updates["profile_picture_url"] = data.profile_picture_url

    # Password change flow — verify current password via Firebase, then update
    if data.new_password is not None:
        if not data.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="current_password is required to change your password.",
            )
        # Use Firebase Auth REST to verify the current password is correct
        _verify_firebase_password(user_data["email"], data.current_password)
        # Update password in Firebase Auth via Admin SDK
        try:
            firebase_auth.update_user(uid, password=data.new_password)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update Firebase password: {str(e)}",
            )

    if user_updates:
        db.collection("users").document(uid).update(user_updates)

    # Doctor-only field updates
    if role in ("doctor", "pending") and (data.specialization is not None or data.location is not None):
        doctor_updates: dict[str, Any] = {}
        if data.specialization is not None:
            doctor_updates["specialization"] = data.specialization.strip()
        if data.location is not None:
            doctor_updates["location"] = data.location.strip()
        if doctor_updates:
            db.collection("doctors").document(uid).update(doctor_updates)

    return _fetch_user_profile(uid)


# ─────────────────────────────────────────────────────────────────────────────
# Forgot Password (Firebase Reset Email Flow)
# ─────────────────────────────────────────────────────────────────────────────

async def forgot_password(email: str) -> dict[str, str]:
    """
    Trigger Firebase's built-in password reset email.

    Always returns a generic message regardless of whether the email is registered
    to prevent email enumeration attacks.
    """
    docs = (
        db.collection("users")
        .where(filter=FieldFilter("email", "==", email))
        .limit(1)
        .get()
    )
    if not docs:
        return {"message": "If this email is registered, a password reset email has been sent."}

    try:
        reset_link = firebase_auth.generate_password_reset_link(email)
        _trigger_firebase_password_reset_email(email, reset_link)
    except firebase_auth.EmailNotFoundError:
        return {"message": "If this email is registered, a password reset email has been sent."}
    except Exception as e:
        if "Failed to generate email action link" in str(e):
            return {"message": "If this email is registered, a password reset email has been sent."}
        print(f"[auth_service] forgot_password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process password reset: {str(e)}",
        )

    return {"message": "If this email is registered, a password reset email has been sent."}


# ─────────────────────────────────────────────────────────────────────────────
# Legacy: Verify OTP [DEPRECATED]
# ─────────────────────────────────────────────────────────────────────────────

async def verify_otp_and_issue_reset_token(data: VerifyOTP) -> dict[str, str]:
    """
    [DEPRECATED] Legacy endpoint retained for backward compatibility.
    Validates an OTP from Firestore and issues a narrow-scoped reset JWT.
    """
    valid = await check_otp(data.email, data.otp)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP.",
        )

    reset_token = create_access_token({"email": data.email, "scope": "password_reset"})
    return {"reset_token": reset_token, "message": "OTP verified. Proceed to reset password."}


# ─────────────────────────────────────────────────────────────────────────────
# Legacy: Reset Password [DEPRECATED]
# ─────────────────────────────────────────────────────────────────────────────

async def reset_password(data: ResetPassword) -> dict[str, str]:
    """
    [DEPRECATED] Legacy endpoint retained for backward compatibility.
    Validates a reset token JWT and updates the password in Firebase Auth.
    """
    payload = verify_token(data.reset_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )
    if payload.get("scope") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is not valid for password reset.",
        )
    if payload.get("email") != data.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token email does not match.",
        )

    docs = (
        db.collection("users")
        .where(filter=FieldFilter("email", "==", data.email))
        .limit(1)
        .get()
    )
    if not docs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    uid = docs[0].to_dict()["uid"]

    try:
        firebase_auth.update_user(uid, password=data.new_password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update Firebase password: {str(e)}",
        )

    await delete_otp(data.email)
    return {"message": "Password reset successfully. You can now log in."}
