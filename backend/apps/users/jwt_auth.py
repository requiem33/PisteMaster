from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from django.conf import settings


def get_token_expiration() -> datetime:
    """Get token expiration time."""
    days = getattr(settings, "JWT_EXPIRATION_DAYS", 7)
    return datetime.now(timezone.utc) + timedelta(days=days)


def create_token(user) -> str:
    """
    Create a JWT token for the given user.

    Args:
        user: User model instance

    Returns:
        JWT token string
    """
    payload = {
        "user_id": str(user.id),
        "username": user.username,
        "role": user.role,
        "exp": get_token_expiration(),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload dict or None if invalid/expired
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_user_id_from_token(token: str) -> Optional[str]:
    """Extract user_id from token."""
    payload = decode_token(token)
    if payload:
        return payload.get("user_id")
    return None
