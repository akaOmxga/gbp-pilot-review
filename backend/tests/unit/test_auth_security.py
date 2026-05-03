from uuid import uuid4

from app.security.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_argon2_roundtrip() -> None:
    h = hash_password("longsecret123")
    assert verify_password("longsecret123", h)
    assert not verify_password("wrong", h)


def test_jwt_access_roundtrip() -> None:
    user_id = uuid4()
    token = create_access_token(user_id, role="client")
    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["role"] == "client"
    assert payload["type"] == "access"


def test_jwt_refresh_roundtrip() -> None:
    user_id = uuid4()
    token = create_refresh_token(user_id)
    payload = decode_token(token)
    assert payload["type"] == "refresh"
