import pytest
from httpx import ASGITransport, AsyncClient

pytestmark = pytest.mark.asyncio

EXPECTED_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "strict-origin-when-cross-origin",
    "permissions-policy": "geolocation=(), microphone=(), camera=()",
    "content-security-policy": "default-src 'self'; frame-ancestors 'none'; base-uri 'none'",
}


async def test_security_headers_set_on_healthz(
    unauthenticated_client: AsyncClient,
) -> None:
    response = await unauthenticated_client.get("/healthz")
    assert response.status_code == 200
    for header, value in EXPECTED_HEADERS.items():
        assert response.headers.get(header) == value, header


async def test_security_headers_set_on_4xx(
    unauthenticated_client: AsyncClient,
) -> None:
    response = await unauthenticated_client.get("/api/v1/me")
    assert response.status_code in (401, 403)
    for header in EXPECTED_HEADERS:
        assert header in response.headers, header


async def test_hsts_absent_in_non_production(
    unauthenticated_client: AsyncClient,
) -> None:
    response = await unauthenticated_client.get("/healthz")
    assert "strict-transport-security" not in response.headers


async def test_hsts_present_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    from app.config import get_settings

    get_settings.cache_clear()
    try:
        from app.main import create_app

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/healthz")
        assert response.headers.get("strict-transport-security", "").startswith("max-age=")
    finally:
        get_settings.cache_clear()


async def test_server_header_stripped(
    unauthenticated_client: AsyncClient,
) -> None:
    response = await unauthenticated_client.get("/healthz")
    assert "server" not in {k.lower() for k in response.headers}
