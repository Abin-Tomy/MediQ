import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from jose import JWTError, jwt

# JWT configuration constants loaded from environment
SECRET_KEY = os.getenv("SECRET_KEY", "mediq-secret-key-default")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Generate a signed short-lived JWT access token.
    Default validity is configured via ACCESS_TOKEN_EXPIRE_MINUTES.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": now, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Generate a signed long-lived JWT refresh token.
    Default validity is configured via REFRESH_TOKEN_EXPIRE_DAYS (7 days).
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "iat": now, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[dict[str, Any]]:
    """
    Decode and validate a JWT signature and expiration.
    Returns the decoded claims dictionary on success, or None if invalid/expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_refresh_token(token: str) -> Optional[dict[str, Any]]:
    """
    Verify token validity and confirm it possesses the 'refresh' token type claim.
    """
    payload = verify_token(token)
    if payload and payload.get("type") == "refresh":
        return payload
    return None


def decode_uid(token: str) -> Optional[str]:
    """
    Extract the subject/uid from a valid JWT token payload.
    """
    payload = verify_token(token)
    if payload:
        return payload.get("uid")
    return None

