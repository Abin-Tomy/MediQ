"""
FastAPI Authentication Dependencies.

Provides injectable dependency functions for:
- Extracting and validating the JWT Bearer token from request headers
- Role-based access control (admin guard)
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.utils.jwt_handler import verify_token

# FastAPI's built-in HTTP Bearer scheme — extracts the token from the
# "Authorization: Bearer <token>" header automatically.
_bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> dict:
    """
    Decode and validate the JWT Bearer token on every protected request.

    Returns the full decoded payload (uid, email, role, etc.) so downstream
    route handlers and services can read identity information without repeating
    token verification logic.

    Raises HTTP 401 if the token is missing, malformed, or expired.
    """
    token = credentials.credentials
    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """
    Guard that restricts an endpoint to admin users only.

    Chains off `get_current_user` — the token is validated first, then the
    role is checked. Raises HTTP 403 if the authenticated user is not an admin.
    """
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return user
