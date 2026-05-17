"""Integration tests for the OAuth Google authorize + callback endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import auth_headers
from tests.factories import create_full_client

pytestmark = pytest.mark.integration


async def test_authorize_returns_redirect_url_and_state(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _c, user, _settings, _sub, _loc, _cred = await create_full_client(db_session)
    r = await client.get(
        "/api/v1/oauth/google/authorize", headers=auth_headers(user.id, role="client")
    )
    assert r.status_code == 200
    body = r.json()
    assert "authorize_url" in body
    assert body["authorize_url"].startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert "state" in body and len(body["state"]) > 30


async def test_authorize_requires_auth(client: AsyncClient) -> None:
    r = await client.get("/api/v1/oauth/google/authorize")
    assert r.status_code == 401


async def test_callback_rejects_invalid_state(client: AsyncClient) -> None:
    r = await client.get("/api/v1/oauth/google/callback?code=x&state=garbage")
    assert r.status_code == 400
