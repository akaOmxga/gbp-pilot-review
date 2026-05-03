import hashlib
import hmac
import os

from app.integrations.lemonsqueezy.webhooks import verify_signature


def _sign(body: bytes) -> str:
    secret = os.environ["LEMONSQUEEZY_WEBHOOK_SECRET"].encode()
    return hmac.new(secret, body, hashlib.sha256).hexdigest()


def test_verify_signature_valid() -> None:
    body = b'{"meta":{"event_name":"order_created"}}'
    sig = _sign(body)
    assert verify_signature(body, sig) is True


def test_verify_signature_invalid() -> None:
    body = b'{"meta":{"event_name":"order_created"}}'
    assert verify_signature(body, "deadbeef" * 8) is False


def test_verify_signature_missing() -> None:
    assert verify_signature(b"any", None) is False
