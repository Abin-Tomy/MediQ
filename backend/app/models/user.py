"""
User and Authentication Pydantic Data Models.

Defines request and response schemas for:
- Role designations (patient, pending, doctor, admin)
- Patient and doctor registration
- Login, Google OAuth, token refresh
- Profile viewing and editing
- Password management
- Admin operations on users and doctors
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class UserRole(str, Enum):
    """Supported authorization roles across the MediQ platform."""
    patient = "patient"
    pending = "pending"   # Doctor application awaiting admin approval
    doctor  = "doctor"
    admin   = "admin"


# ─────────────────────────────────────────────────────────────────────────────
# Registration Schemas
# ─────────────────────────────────────────────────────────────────────────────

class PatientRegister(BaseModel):
    """Payload for patient self-registration. Role is automatically set to 'patient'."""
    name: str
    email: EmailStr
    password: str
    phone_number: Optional[str] = None
    profile_picture_url: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        """Enforce minimum password length."""
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return value

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, value: str) -> str:
        """Enforce non-empty name after trimming whitespace."""
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Name cannot be empty or whitespace only")
        return trimmed


class DoctorRegister(BaseModel):
    """
    Payload for doctor self-registration.
    Role is set to 'pending' until an admin approves the application.
    The Flutter client uploads license and profile photo to Firebase Storage
    and sends the resulting download URLs here.
    """
    name: str
    email: EmailStr
    password: str
    phone_number: Optional[str] = None
    specialization: str
    location: str
    license_document_url: str           # Firebase Storage download URL
    profile_picture_url: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return value

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Name cannot be empty or whitespace only")
        return trimmed

    @field_validator("specialization", "location")
    @classmethod
    def validate_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Field cannot be empty")
        return value.strip()


# ─────────────────────────────────────────────────────────────────────────────
# Login Schema
# ─────────────────────────────────────────────────────────────────────────────

class UserLogin(BaseModel):
    """Payload for email/password authentication. Works for all roles."""
    email: EmailStr
    password: str


# ─────────────────────────────────────────────────────────────────────────────
# OAuth Schema
# ─────────────────────────────────────────────────────────────────────────────

class GoogleAuthRequest(BaseModel):
    """Firebase ID token received from the Flutter Google Sign-In SDK."""
    id_token: str


# ─────────────────────────────────────────────────────────────────────────────
# Token Schemas
# ─────────────────────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    """JWT response returning a signed access and refresh token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Payload to exchange a valid refresh token for a new access token."""
    refresh_token: str


class TokenData(BaseModel):
    """Decoded claim payload stored inside authenticated JWT tokens."""
    uid: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Profile Schemas
# ─────────────────────────────────────────────────────────────────────────────

class DoctorProfileResponse(BaseModel):
    """Doctor-specific fields stored in the 'doctors' Firestore collection."""
    specialization: Optional[str] = None
    location: Optional[str] = None
    available_slots: list = []
    rating: Optional[float] = None
    is_approved: bool = False
    license_document_url: Optional[str] = None


class UserProfileResponse(BaseModel):
    """
    Full user profile returned by GET /auth/me and admin user endpoints.
    Includes doctor-specific fields merged in when the user's role is 'doctor'.
    """
    uid: str
    name: str
    email: str
    role: str
    phone_number: Optional[str] = None
    profile_picture_url: Optional[str] = None
    is_email_verified: bool = False
    is_active: bool = True
    created_at: Optional[str] = None
    # Doctor-specific fields (None for non-doctors)
    doctor_profile: Optional[DoctorProfileResponse] = None


class UpdateProfile(BaseModel):
    """
    Payload for PATCH /auth/me.
    All fields are optional — only supplied fields are updated.
    Doctors can additionally update specialization and location.
    Password change requires supplying both current_password and new_password.
    """
    name: Optional[str] = None
    phone_number: Optional[str] = None
    profile_picture_url: Optional[str] = None
    # Doctor-only fields
    specialization: Optional[str] = None
    location: Optional[str] = None
    # Password change
    current_password: Optional[str] = None
    new_password: Optional[str] = None

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and len(value) < 8:
            raise ValueError("New password must be at least 8 characters long")
        return value


# ─────────────────────────────────────────────────────────────────────────────
# Admin Operation Schemas
# ─────────────────────────────────────────────────────────────────────────────

class AdminAddDoctor(BaseModel):
    """
    Payload for POST /admin/doctors (admin manually creates a doctor account).
    Role is immediately set to 'doctor'. Firebase sends the doctor a
    password-reset email so they can set their own credentials.
    """
    name: str
    email: EmailStr
    specialization: str
    location: str
    phone_number: Optional[str] = None

    @field_validator("name", "specialization", "location")
    @classmethod
    def validate_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Field cannot be empty")
        return value.strip()


class AdminUpdateUser(BaseModel):
    """Payload for PATCH /admin/users/{uid} — admin can change role or active status."""
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


# ─────────────────────────────────────────────────────────────────────────────
# Password Reset Schemas (active + legacy)
# ─────────────────────────────────────────────────────────────────────────────

class ForgotPassword(BaseModel):
    """Request schema to trigger a Firebase password reset email."""
    email: EmailStr


class VerifyOTP(BaseModel):
    """[LEGACY] Request schema to verify a 6-digit OTP code."""
    email: EmailStr
    otp: str


class ResetPassword(BaseModel):
    """[LEGACY] Request schema to set a new password using a reset token."""
    email: EmailStr
    new_password: str
    reset_token: str

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("New password must be at least 8 characters long")
        return value


# ─────────────────────────────────────────────────────────────────────────────
# Common Response Schemas
# ─────────────────────────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    """Standard generic operational status message response."""
    message: str
    success: bool = True
