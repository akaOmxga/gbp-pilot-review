"""GDPR Art. 15 — droit d'accès export endpoint."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import auth_headers
from tests.factories import (
    build_response,
    build_review,
    create_full_client,
)

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_export_returns_owner_data(client: AsyncClient, db_session: AsyncSession) -> None:
    _business, user, _settings, _sub, location, _cred = await create_full_client(
        db_session, business_name="Owner Corp"
    )
    review = build_review(location_id=location.id, comment="Excellent !")
    db_session.add(review)
    await db_session.flush()
    response = build_response(review_id=review.id, content="Merci beaucoup !")
    db_session.add(response)
    await db_session.commit()

    res = await client.get("/api/v1/me/export", headers=auth_headers(user.id))
    assert res.status_code == 200
    payload = res.json()

    assert payload["user"]["email"] == user.email
    assert "password_hash" not in payload["user"]
    assert payload["client"]["business_name"] == "Owner Corp"
    assert payload["client_settings"] is not None
    assert payload["subscription"] is not None
    assert payload["notification_preference"] is not None
    assert any(loc["id"] == str(location.id) for loc in payload["locations"])
    assert any(r["comment"] == "Excellent !" for r in payload["reviews"])
    assert any(r["content"] == "Merci beaucoup !" for r in payload["responses"])


async def test_export_isolated_per_user(client: AsyncClient, db_session: AsyncSession) -> None:
    _b1, user_a, _s1, _sub1, _loc_a, _c1 = await create_full_client(
        db_session, business_name="Alpha"
    )
    _b2, _user_b, _s2, _sub2, loc_b, _c2 = await create_full_client(
        db_session, business_name="Beta"
    )
    review_b = build_review(location_id=loc_b.id, google_review_id="ext-b-1")
    db_session.add(review_b)
    await db_session.commit()

    res = await client.get("/api/v1/me/export", headers=auth_headers(user_a.id))
    assert res.status_code == 200
    payload = res.json()
    assert payload["client"]["business_name"] == "Alpha"
    assert all(loc["id"] != str(loc_b.id) for loc in payload["locations"])
    assert all(r["google_review_id"] != "ext-b-1" for r in payload["reviews"])


async def test_export_requires_auth(client: AsyncClient) -> None:
    res = await client.get("/api/v1/me/export")
    assert res.status_code == 401
