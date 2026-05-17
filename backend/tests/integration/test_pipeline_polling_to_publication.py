"""End-to-end pipeline integration test: polling → filtering → generation → publication.

Uses real DB + mocked external providers (Google + Claude). Verifies state
transitions across services.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.google_business.schemas import GoogleReview
from app.models.enums import (
    ResponseStatus,
    ReviewStatus,
)
from app.models.prompt_version import PromptVersion
from app.services.filtering_service import FilterDecision, FilteringService
from app.services.generation_service import GenerationService
from app.services.polling_service import PollingService
from app.services.publication_service import PublicationService
from tests.factories import create_full_client

pytestmark = pytest.mark.integration


async def _seed_prompt(session: AsyncSession) -> None:
    session.add(
        PromptVersion(
            version="v1",
            system_prompt="You are a reply assistant.",
            user_prompt_template="Reply to: $review_comment",
            model="claude-sonnet-4-6",
            temperature=Decimal("0.70"),
            max_tokens=600,
            is_active=True,
        )
    )
    await session.flush()


async def test_full_pipeline_polling_to_publication(
    db_session: AsyncSession,
    mock_google_adapter: AsyncMock,
    mock_llm_provider: AsyncMock,
) -> None:
    client, user, _settings, _sub, location, _cred = await create_full_client(db_session)
    await _seed_prompt(db_session)

    # 1. Polling — Google returns 1 review
    now = datetime.now(UTC)
    google_review = GoogleReview(
        name=f"accounts/12345/locations/{location.google_location_id}/reviews/google-r-1",
        review_id="google-r-1",
        reviewer_display_name="Alice",
        rating=5,
        comment="Une expérience exceptionnelle, je recommande chaleureusement à tous mes amis.",
        create_time=now,
    )
    mock_google_adapter.list_reviews = AsyncMock(return_value=([google_review], None))

    polling = PollingService(db_session, adapter=mock_google_adapter)
    new_ids = await polling.poll_client(client.id)
    assert len(new_ids) == 1
    review_id = new_ids[0]

    # 2. Filtering — 5★ with text → PROCESSING
    decision = await FilteringService(db_session).decide(review_id)
    assert decision == FilterDecision.PROCESSING

    from app.models.review import Review

    review = await db_session.get(Review, review_id)
    assert review is not None
    assert review.status == ReviewStatus.processing

    # 3. Generation — Claude mock returns valid content
    gen = GenerationService(db_session, provider=mock_llm_provider)
    response = await gen.generate_for_review(review_id)
    assert response.status == ResponseStatus.pending_validation_client
    refreshed = await db_session.get(Review, review_id)
    assert refreshed is not None
    assert refreshed.status == ReviewStatus.awaiting_response

    # 4. Scheduling (manual validation)
    pub = PublicationService(db_session, adapter=mock_google_adapter)
    scheduled = await pub.schedule_publication(response.id, validated_by_user_id=user.id)
    assert scheduled.status == ResponseStatus.scheduled

    # 5. Publication — bypass undo window, then publish_now
    scheduled.undo_deadline_at = datetime.now(UTC) - timedelta(minutes=1)
    scheduled.scheduled_at = datetime.now(UTC) - timedelta(minutes=10)
    await db_session.flush()

    published = await pub.publish_now(scheduled)
    assert published.status == ResponseStatus.published
    mock_google_adapter.reply_to_review.assert_awaited_once()

    completed = await db_session.get(Review, review_id)
    assert completed is not None
    assert completed.status == ReviewStatus.completed
