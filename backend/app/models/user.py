from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from enum import Enum


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class UserRole(str, Enum):
    patient = "patient"
    doctor  = "doctor"
    admin   = "admin"


# ─────────────────────────────────────────────
# Registration & Login
# ─────────────────────────────────────────────

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone_number: Optional[str] = None
    role: UserRole = UserRole.patient          # default → patient

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ─────────────────────────────────────────────
# Google OAuth
# ─────────────────────────────────────────────

class GoogleAuth(BaseModel):
    """Receives the Firebase ID Token from the Flutter/frontend Google Sign-In"""
    id_token: str


# ─────────────────────────────────────────────
# Token Models
# ─────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Decoded payload stored inside a JWT"""
    uid: Optional[str]   = None
    email: Optional[str] = None
    role: Optional[str]  = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ─────────────────────────────────────────────
# User Response (what we return to the client)
# ─────────────────────────────────────────────

class UserResponse(BaseModel):
    uid: str
    name: str
    email: str
    role: str = "patient"
    phone_number: Optional[str] = None
    is_email_verified: bool     = False
    created_at: Optional[str]   = None
    profile_picture: Optional[str] = None


# ─────────────────────────────────────────────
# Profile Update
# ─────────────────────────────────────────────

class UserUpdate(BaseModel):
    name: Optional[str]           = None
    phone_number: Optional[str]   = None
    profile_picture: Optional[str] = None   # URL to photo


# ─────────────────────────────────────────────
# Password Management
# ─────────────────────────────────────────────

class ForgotPassword(BaseModel):
    email: EmailStr

class ResendOTP(BaseModel):
    email: EmailStr

class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str

class ResetPassword(BaseModel):
    email: EmailStr
    new_password: str
    reset_token: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("New password must be at least 8 characters")
        return v

class ChangePassword(BaseModel):
    """For logged-in users who remember their old password"""
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("New password must be at least 8 characters")
        return v


# ─────────────────────────────────────────────
# Generic API Response
# ─────────────────────────────────────────────

class MessageResponse(BaseModel):
    """Standard success/info message response"""
    message: str
    success: bool = True
