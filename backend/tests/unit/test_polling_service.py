"""Unit tests for PollingService — uses real DB + mocked Google adapter."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.google_business.exceptions import GoogleAuthError
from app.integrations.google_business.schemas import GoogleReview
from app.models.enums import OAuthCredentialStatus
from app.services.polling_service import PollingService
from tests.factories import build_oauth_credential, build_review, create_full_client

pytestmark = pytest.mark.integration


def _make_google_review(rid: str, rating: int = 5) -> GoogleReview:
    return GoogleReview(
        name=f"accounts/1/locations/2/reviews/{rid}",
        review_id=rid,
        reviewer_display_name="Jane Doe",
        rating=rating,
        comment="Great service.",
        create_time=datetime.now(UTC),
    )


async def test_poll_inserts_new_reviews(
    db_session: AsyncSession, mock_google_adapter: AsyncMock
) -> None:
    client, _user, _settings, _sub, _location, _cred = await create_full_client(db_session)
    mock_google_adapter.list_reviews = AsyncMock(
        return_value=([_make_google_review("r-1"), _make_google_review("r-2")], None)
    )
    service = PollingService(db_session, adapter=mock_google_adapter)
    new_ids = await service.poll_client(client.id)
    assert len(new_ids) == 2


async def test_poll_dedupes_existing_reviews(
    db_session: AsyncSession, mock_google_adapter: AsyncMock
) -> None:
    client, _user, _settings, _sub, location, _cred = await create_full_client(db_session)
    existing = build_review(location_id=location.id, google_review_id="r-existing")
    db_session.add(existing)
    await db_session.flush()

    mock_google_adapter.list_reviews = AsyncMock(
        return_value=([_make_google_review("r-existing"), _make_google_review("r-new")], None)
    )
    service = PollingService(db_session, adapter=mock_google_adapter)
    new_ids = await service.poll_client(client.id)
    assert len(new_ids) == 1


async def test_poll_no_oauth_returns_empty(
    db_session: AsyncSession, mock_google_adapter: AsyncMock
) -> None:
    from tests.factories import build_client

    client = build_client()
    db_session.add(client)
    await db_session.flush()

    service = PollingService(db_session, adapter=mock_google_adapter)
    assert await service.poll_client(client.id) == []
    mock_google_adapter.list_reviews.assert_not_called()


async def test_poll_revokes_credential_on_auth_error(
    db_session: AsyncSession, mock_google_adapter: AsyncMock
) -> None:
    client, _user, _settings, _sub, _location, credential = await create_full_client(db_session)
    mock_google_adapter.list_reviews = AsyncMock(side_effect=GoogleAuthError("invalid"))

    service = PollingService(db_session, adapter=mock_google_adapter)
    with pytest.raises(GoogleAuthError):
        await service.poll_client(client.id)
    await db_session.refresh(credential)
    assert credential.status == OAuthCredentialStatus.revoked


async def test_poll_skips_revoked_credential(
    db_session: AsyncSession, mock_google_adapter: AsyncMock
) -> None:
    from tests.factories import build_client, build_location

    client = build_client()
    db_session.add(client)
    await db_session.flush()
    db_session.add(build_location(client_id=client.id))
    db_session.add(
        build_oauth_credential(client_id=client.id, status=OAuthCredentialStatus.revoked)
    )
    await db_session.flush()

    service = PollingService(db_session, adapter=mock_google_adapter)
    assert await service.poll_client(client.id) == []
