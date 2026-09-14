"""
OTP (One-Time Password) Handler Utility.
Maintained for backward-compatible verification and cleanup in legacy endpoints.
"""

import random
import string
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.database import db


def generate_otp(length: int = 6) -> str:
    """
    Generate a cryptographically suitable random numeric OTP string.
    """
    return "".join(random.choices(string.digits, k=length))


async def store_otp(email: str, otp: str, ttl_minutes: int = 10) -> None:
    """
    Persist an OTP code for an email in Firestore with an expiration timestamp.
    """
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
    db.collection("otps").document(email).set({
        "otp": otp,
        "expires_at": expires_at,
        "used": False,
        "created_at": datetime.now(timezone.utc),
    })


async def verify_otp(email: str, otp: str) -> bool:
    """
    Verify an OTP code against Firestore records.
    Returns True only if the record exists, matches the code, is unused, and unexpired.
    Marks the code as used immediately to mitigate replay attempts.
    """
    doc_ref = db.collection("otps").document(email)
    doc = doc_ref.get()

    if not doc.exists:
        return False

    data = doc.to_dict() or {}

    # Check if already consumed
    if data.get("used", False):
        return False

    # Check expiration
    expires_at: Optional[datetime] = data.get("expires_at")
    if expires_at is None:
        return False

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires_at:
        return False

    # Check OTP code match
    if data.get("otp") != otp:
        return False

    # Mark as used to prevent subsequent verification of the same code
    doc_ref.update({"used": True})
    return True


async def delete_otp(email: str) -> None:
    """
    Remove OTP document from Firestore once the reset cycle finishes.
    """
    db.collection("otps").document(email).delete()


async def is_otp_pending(email: str) -> bool:
    """
    Check whether an active (unused and unexpired) OTP exists for an email.
    """
    doc = db.collection("otps").document(email).get()
    if not doc.exists:
        return False

    data = doc.to_dict() or {}
    if data.get("used", False):
        return False

    expires_at: Optional[datetime] = data.get("expires_at")
    if expires_at is None:
        return False

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    return datetime.now(timezone.utc) < expires_at

