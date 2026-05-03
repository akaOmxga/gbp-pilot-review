from urllib.parse import parse_qs, urlparse

from app.services.oauth_service import (
    GOOGLE_AUTHORIZE_URL,
    SCOPE_BUSINESS_MANAGE,
    build_authorize_url,
    generate_state,
)


def test_authorize_url_contains_required_params() -> None:
    url = build_authorize_url(state="abc123")
    parsed = urlparse(url)
    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == GOOGLE_AUTHORIZE_URL
    qs = parse_qs(parsed.query)
    assert qs["scope"] == [SCOPE_BUSINESS_MANAGE]
    assert qs["access_type"] == ["offline"]
    assert qs["prompt"] == ["consent"]
    assert qs["state"] == ["abc123"]
    assert qs["response_type"] == ["code"]


def test_state_is_high_entropy() -> None:
    a, b = generate_state(), generate_state()
    assert a != b
    assert len(a) >= 32
