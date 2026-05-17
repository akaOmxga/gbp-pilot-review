from app.logging_config import _patch_record, _redact


def _make_record(message: str, **extra: object) -> dict:  # type: ignore[type-arg]
    return {"message": message, "extra": dict(extra)}


def test_redact_bearer_tokens() -> None:
    assert _redact("Authorization: Bearer abc123XYZ_-.") == "Authorization: Bearer ***"


def test_redact_jwt_in_message() -> None:
    jwt = "eyJabc.eyJpc3MiOiJ4eXoifQ.signaturepart"
    assert _redact(f"token={jwt}") == "token=***JWT***"


def test_patch_record_masks_sensitive_extras() -> None:
    record = _make_record("login attempt", password="hunter2", token="secret-x")
    _patch_record(record)  # type: ignore[no-untyped-call]
    assert record["extra"]["password"] == "***"
    assert record["extra"]["token"] == "***"


def test_patch_record_redacts_bearer_in_message_field() -> None:
    record = _make_record("got Bearer abc.def.ghi from upstream")
    _patch_record(record)  # type: ignore[no-untyped-call]
    assert "Bearer ***" in record["message"]
    assert "abc.def.ghi" not in record["message"]


def test_non_sensitive_extras_untouched() -> None:
    record = _make_record("ok", user_id="u-123")
    _patch_record(record)  # type: ignore[no-untyped-call]
    assert record["extra"]["user_id"] == "u-123"
