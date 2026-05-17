"""Unit tests for PublicationService — schedule + cancel + publish_now."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.google_business.exceptions import GoogleAuthError
from app.models.enums import (
    OAuthCredentialStatus,
    ResponseStatus,
    ReviewStatus,
)
from app.services.publication_service import PublicationService
from tests.factories import build_response, build_review, create_full_client

pytestmark = pytest.mark.integration


async def test_schedule_publication_sets_scheduled_at_and_validator(
    db_session: AsyncSession, mock_google_adapter: AsyncMock
) -> None:
    _client, user, _settings, _sub, location, _cred = await create_full_client(db_session)
    review = build_review(location_id=location.id)
    db_session.add(review)
    await db_session.flush()
    response = build_response(review_id=review.id)
    db_session.add(response)
    await db_session.flush()

    service = PublicationService(db_session, adapter=mock_google_adapter)
    result = await service.schedule_publication(response.id, validated_by_user_id=user.id)

    assert result.status == ResponseStatus.scheduled
    assert result.scheduled_at is not None
    assert result.undo_deadline_at is not None
    assert result.validated_by_user_id == user.id
    assert result.validated_at is not None


async def test_schedule_from_wrong_status_raises_409(
    db_session: AsyncSession, mock_google_adapter: AsyncMock
) -> None:
    _client, user, _settings, _sub, location, _cred = await create_full_client(db_session)
    review = build_review(location_id=location.id)
    db_session.add(review)
    await db_session.flush()
    response = build_response(review_id=review.id, status=ResponseStatus.published)
    db_session.add(response)
    await db_session.flush()

    service = PublicationService(db_session, adapter=mock_google_adapter)
    with pytest.raises(HTTPException) as exc:
        await service.schedule_publication(response.id, validated_by_user_id=user.id)
    assert exc.value.status_code == 409


async def test_cancel_within_undo_window(
    db_session: AsyncSession, mock_google_adapter: AsyncMock
) -> None:
    _client, _user, _settings, _sub, location, _cred = await create_full_client(db_session)
    review = build_review(location_id=location.id)
    db_session.add(review)
    await db_session.flush()
    response = build_response(review_id=review.id, status=ResponseStatus.scheduled)
    response.scheduled_at = datetime.now(UTC) + timedelta(hours=1)
    response.undo_deadline_at = datetime.now(UTC) + timedelta(minutes=5)
    db_session.add(response)
    await db_session.flush()

    service = PublicationService(db_session, adapter=mock_google_adapter)
    cancelled = await service.cancel_publication(response.id)
    assert cancelled.status == ResponseStatus.cancelled
    assert cancelled.is_active is False


async def test_cancel_after_undo_window_410(
    db_session: AsyncSession, mock_google_adapter: AsyncMock
) -> None:
    _client, _user, _settings, _sub, location, _cred = await create_full_client(db_session)
    review = build_review(location_id=location.id)
    db_session.add(review)
    await db_session.flush()
    response = build_response(review_id=review.id, status=ResponseStatus.scheduled)
    response.scheduled_at = datetime.now(UTC) + timedelta(hours=1)
    response.undo_deadline_at = datetime.now(UTC) - timedelta(minutes=1)
    db_session.add(response)
    await db_session.flush()

    service = PublicationService(db_session, adapter=mock_google_adapter)
    with pytest.raises(HTTPException) as exc:
        await service.cancel_publication(response.id)
    assert exc.value.status_code == 410


async def test_publish_now_happy_path(
    db_session: AsyncSession, mock_google_adapter: AsyncMock
) -> None:
    _client, _user, _settings, _sub, location, _cred = await create_full_client(db_session)
    review = build_review(location_id=location.id)
    db_session.add(review)
    await db_session.flush()
    response = build_response(review_id=review.id, status=ResponseStatus.scheduled)
    response.scheduled_at = datetime.now(UTC) - timedelta(minutes=10)
    response.undo_deadline_at = datetime.now(UTC) - timedelta(minutes=1)
    db_session.add(response)
    await db_session.flush()

    service = PublicationService(db_session, adapter=mock_google_adapter)
    published = await service.publish_now(response)
    assert published.status == ResponseStatus.published
    assert published.published_at is not None
    mock_google_adapter.reply_to_review.assert_awaited_once()
    refreshed_review = await db_session.get(type(review), review.id)
    assert refreshed_review is not None
    assert refreshed_review.status == ReviewStatus.completed


async def test_publish_now_oauth_revoked_rollback(
    db_session: AsyncSession, mock_google_adapter: AsyncMock
) -> None:
    _client, _user, _settings, _sub, location, credential = await create_full_client(db_session)
    review = build_review(location_id=location.id)
    db_session.add(review)
    await db_session.flush()
    response = build_response(review_id=review.id, status=ResponseStatus.scheduled)
    response.scheduled_at = datetime.now(UTC) - timedelta(minutes=10)
    response.undo_deadline_at = datetime.now(UTC) - timedelta(minutes=1)
    db_session.add(response)
    await db_session.flush()

    mock_google_adapter.reply_to_review = AsyncMock(side_effect=GoogleAuthError("revoked"))
    service = PublicationService(db_session, adapter=mock_google_adapter)
    result = await service.publish_now(response)

    assert result.status == ResponseStatus.scheduled
    assert credential.status == OAuthCredentialStatus.revoked


async def test_publish_now_unknown_failure_marks_failed(
    db_session: AsyncSession, mock_google_adapter: AsyncMock
) -> None:
    _client, _user, _settings, _sub, location, _cred = await create_full_client(db_session)
    review = build_review(location_id=location.id)
    db_session.add(review)
    await db_session.flush()
    response = build_response(review_id=review.id, status=ResponseStatus.scheduled)
    response.scheduled_at = datetime.now(UTC) - timedelta(minutes=10)
    response.undo_deadline_at = datetime.now(UTC) - timedelta(minutes=1)
    db_session.add(response)
    await db_session.flush()

    mock_google_adapter.reply_to_review = AsyncMock(side_effect=RuntimeError("HTTP 500"))
    service = PublicationService(db_session, adapter=mock_google_adapter)
    with pytest.raises(RuntimeError):
        await service.publish_now(response)
    assert response.status == ResponseStatus.failed
    assert response.failure_reason is not None


async def test_schedule_missing_response_404(
    db_session: AsyncSession, mock_google_adapter: AsyncMock
) -> None:
    service = PublicationService(db_session, adapter=mock_google_adapter)
    with pytest.raises(HTTPException) as exc:
        await service.schedule_publication(uuid4(), validated_by_user_id=uuid4())
    assert exc.value.status_code == 404
