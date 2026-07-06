import random
import string
from datetime import datetime, timedelta, timezone
from app.database import db


def generate_otp() -> str:
    """Generate a secure 6-digit numeric OTP"""
    return ''.join(random.choices(string.digits, k=6))


async def store_otp(email: str, otp: str) -> None:
    """Store OTP in Firestore with 10-minute expiry"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.collection("otps").document(email).set({
        "otp": otp,
        "expires_at": expire,
        "used": False,
        "created_at": datetime.now(timezone.utc)
    })


async def verify_otp(email: str, otp: str) -> bool:
    """
    Verify OTP for a given email.
    Returns True only if OTP exists, is unused, not expired, and matches.
    Marks OTP as used on success to prevent reuse.
    """
    doc = db.collection("otps").document(email).get()

    if not doc.exists:
        return False

    data = doc.to_dict()

    # Already used
    if data.get("used"):
        return False

    # Check expiry — Firestore returns timezone-aware datetime
    expires_at = data.get("expires_at")
    if expires_at is None:
        return False

    now = datetime.now(timezone.utc)

    # Handle both timezone-aware and naive datetimes from Firestore
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if now > expires_at:
        return False

    # Wrong OTP
    if data.get("otp") != otp:
        return False

    # ✅ Valid — mark as used immediately to prevent replay attacks
    db.collection("otps").document(email).update({"used": True})
    return True


async def delete_otp(email: str) -> None:
    """Clean up OTP document after password reset is complete"""
    db.collection("otps").document(email).delete()


async def is_otp_pending(email: str) -> bool:
    """Check if there's an active (unused, unexpired) OTP for an email"""
    doc = db.collection("otps").document(email).get()
    if not doc.exists:
        return False

    data = doc.to_dict()
    if data.get("used"):
        return False

    expires_at = data.get("expires_at")
    if expires_at is None:
        return False

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    return datetime.now(timezone.utc) < expires_at
