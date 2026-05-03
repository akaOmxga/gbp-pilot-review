import hashlib
import hmac

from app.config import get_settings


def verify_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """Verify HMAC-SHA256 signature on a raw Lemon Squeezy webhook body.

    Header convention: `X-Signature: <hex>`.
    """
    if not signature_header:
        return False
    settings = get_settings()
    secret = settings.lemonsqueezy_webhook_secret.get_secret_value().encode()
    digest = hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature_header)
