from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import get_settings

_hasher = PasswordHasher()


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, plain)
    except VerifyMismatchError:
        return False


def needs_rehash(hashed: str) -> bool:
    return _hasher.check_needs_rehash(hashed)


def _now() -> datetime:
    return datetime.now(UTC)


def create_access_token(user_id: UUID, role: str, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": _now(),
        "exp": _now() + timedelta(minutes=settings.jwt_access_ttl_minutes),
    }
    if extra:
        payload.update(extra)
    encoded = jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm="HS256")
    return encoded if isinstance(encoded, str) else encoded.decode()


def create_refresh_token(user_id: UUID) -> str:
    settings = get_settings()
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": _now(),
        "exp": _now() + timedelta(days=settings.jwt_refresh_ttl_days),
    }
    encoded = jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm="HS256")
    return encoded if isinstance(encoded, str) else encoded.decode()


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret.get_secret_value(), algorithms=["HS256"])


def create_email_verification_token(user_id: UUID) -> str:
    settings = get_settings()
    payload = {
        "sub": str(user_id),
        "type": "email_verify",
        "iat": _now(),
        "exp": _now() + timedelta(days=2),
    }
    encoded = jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm="HS256")
    return encoded if isinstance(encoded, str) else encoded.decode()


def create_password_reset_token(user_id: UUID) -> str:
    settings = get_settings()
    payload = {
        "sub": str(user_id),
        "type": "password_reset",
        "iat": _now(),
        "exp": _now() + timedelta(hours=1),
    }
    encoded = jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm="HS256")
    return encoded if isinstance(encoded, str) else encoded.decode()
