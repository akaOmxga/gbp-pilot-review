from typing import Any

from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from sqlalchemy import LargeBinary
from sqlalchemy.types import TypeDecorator

from app.config import get_settings


def _build_fernet() -> MultiFernet:
    settings = get_settings()
    keys = [Fernet(settings.oauth_token_encryption_key.get_secret_value().encode())]
    return MultiFernet(keys)


_fernet: MultiFernet | None = None


def _get_fernet() -> MultiFernet:
    global _fernet
    if _fernet is None:
        _fernet = _build_fernet()
    return _fernet


def encrypt(value: str) -> bytes:
    return _get_fernet().encrypt(value.encode())


def decrypt(value: bytes) -> str:
    try:
        return _get_fernet().decrypt(value).decode()
    except InvalidToken as exc:
        raise ValueError("Could not decrypt value (invalid Fernet token)") from exc


class EncryptedString(TypeDecorator[str]):
    """Stores a string transparently encrypted with Fernet (BYTEA on disk)."""

    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect: Any) -> bytes | None:
        if value is None:
            return None
        return encrypt(value)

    def process_result_value(self, value: bytes | None, dialect: Any) -> str | None:
        if value is None:
            return None
        return decrypt(value)
