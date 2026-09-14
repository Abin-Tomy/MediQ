"""
Authentication API Routes.

Exposes REST endpoints for:
- Patient registration  (POST /auth/register/patient)
- Doctor registration   (POST /auth/register/doctor)
- Login for all roles   (POST /auth/login)
- Google OAuth login    (POST /auth/google)
- Token refresh         (POST /auth/refresh)
- Firebase reset email  (POST /auth/forgot-password)
- Current user profile  (GET  /auth/me)
- Update own profile    (PATCH /auth/me)
- Deprecated OTP routes (POST /auth/verify-otp, POST /auth/reset-password)
"""

from fastapi import APIRouter, Depends, status

from app.models.user import (
    AdminAddDoctor,
    DoctorRegister,
    ForgotPassword,
    GoogleAuthRequest,
    PatientRegister,
    RefreshTokenRequest,
    ResetPassword,
    TokenResponse,
    UpdateProfile,
    UserLogin,
    UserProfileResponse,
    VerifyOTP,
)
from app.services.auth_service import (
    forgot_password,
    get_me,
    google_login,
    login_user,
    refresh_access_token,
    register_doctor,
    register_patient,
    reset_password,
    update_me,
    verify_otp_and_issue_reset_token,
)
from app.utils.auth_dependencies import get_current_user

router = APIRouter(tags=["Auth"])


# ─────────────────────────────────────────────────────────────────────────────
# Registration Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/register/patient",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register as a patient",
)
async def register_patient_route(data: PatientRegister):
    """
    Register a new patient account.
    Role is automatically set to 'patient'. Returns a JWT token pair on success.
    """
    return await register_patient(data)


@router.post(
    "/register/doctor",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register as a doctor (pending approval)",
)
async def register_doctor_route(data: DoctorRegister):
    """
    Register a new doctor application.

    Role is set to 'pending' until an admin reviews and approves the submission.
    The request must include Firebase Storage URLs for the medical license document
    and optionally a profile photo — uploaded directly from Flutter to Firebase Storage.
    Returns a JWT with role='pending'.
    """
    return await register_doctor(data)


# ─────────────────────────────────────────────────────────────────────────────
# Login Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login with email and password",
)
async def login(data: UserLogin):
    """
    Authenticate with email and password. Works for all roles (patient, doctor, admin).
    Returns a JWT access and refresh token pair with the user's current role embedded.
    Deactivated accounts receive a 403 response.
    """
    return await login_user(data)


@router.post(
    "/google",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login or register via Google OAuth",
)
async def google_auth(data: GoogleAuthRequest):
    """
    Authenticate using a Firebase ID token from Flutter's Google Sign-In SDK.
    Auto-creates a 'patient' profile in Firestore on first sign-in.
    Subsequent calls return updated tokens for the existing account.
    """
    return await google_login(data)


# ─────────────────────────────────────────────────────────────────────────────
# Token Refresh
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
)
async def refresh_token(data: RefreshTokenRequest):
    """
    Exchange a valid refresh token for a new access + refresh token pair.
    The new token reflects any role changes made since the last login
    (e.g., a pending doctor who was approved will now get role='doctor').
    """
    return await refresh_access_token(data.refresh_token)


# ─────────────────────────────────────────────────────────────────────────────
# Current User Profile
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
)
async def get_current_user_profile(user: dict = Depends(get_current_user)):
    """
    Return the full Firestore profile of the currently authenticated user.
    For doctors and pending applicants, doctor-specific fields are included
    (specialization, location, license URL, approval status).
    """
    return await get_me(user["uid"])


@router.patch(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
)
async def update_current_user_profile(
    data: UpdateProfile,
    user: dict = Depends(get_current_user),
):
    """
    Update the authenticated user's own profile. All fields are optional.

    - Any user: name, phone_number, profile_picture_url
    - Doctors / pending: also specialization, location
    - Password change: requires current_password + new_password (min 8 chars)
    """
    return await update_me(user["uid"], user["role"], data)


# ─────────────────────────────────────────────────────────────────────────────
# Password Reset
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Send Firebase password reset email",
)
async def forgot_password_route(data: ForgotPassword):
    """
    Trigger Firebase's built-in password reset email.
    Always returns a generic message to prevent email enumeration.
    """
    return await forgot_password(data.email)


# ─────────────────────────────────────────────────────────────────────────────
# Deprecated Legacy Routes
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/verify-otp",
    deprecated=True,
    status_code=status.HTTP_200_OK,
    summary="[DEPRECATED] Verify OTP code",
)
async def verify_otp_route(data: VerifyOTP):
    """[DEPRECATED] Legacy OTP verification. Superseded by Firebase reset email flow."""
    return await verify_otp_and_issue_reset_token(data)


@router.post(
    "/reset-password",
    deprecated=True,
    status_code=status.HTTP_200_OK,
    summary="[DEPRECATED] Reset password with token",
)
async def reset_password_route(data: ResetPassword):
    """[DEPRECATED] Legacy password reset with JWT token. Superseded by Firebase reset email flow."""
    return await reset_password(data)
