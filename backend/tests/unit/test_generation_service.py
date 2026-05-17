"""Unit tests for GenerationService — uses real DB + mocked LLM provider."""

from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.claude.adapter import LLMResponse
from app.models.enums import (
    ResponseStatus,
    ReviewStatus,
    ValidationMode,
)
from app.models.prompt_version import PromptVersion
from app.services.generation_service import GenerationService
from app.services.quota_service import QuotaExhaustedError
from tests.factories import (
    build_review,
    create_full_client,
)

pytestmark = pytest.mark.integration


async def _seed_prompt(session: AsyncSession) -> PromptVersion:
    from decimal import Decimal

    version = PromptVersion(
        version="v1",
        system_prompt="You are a helpful business reply assistant.",
        user_prompt_template="Reply to the review: $review_comment",
        model="claude-sonnet-4-6",
        temperature=Decimal("0.70"),
        max_tokens=600,
        is_active=True,
    )
    session.add(version)
    await session.flush()
    return version


async def test_generate_routes_to_client_validation_in_suggestion_mode(
    db_session: AsyncSession, mock_llm_provider: AsyncMock
) -> None:
    _client, _user, _settings, _sub, location, _cred = await create_full_client(
        db_session, validation_mode=ValidationMode.suggestion
    )
    await _seed_prompt(db_session)
    review = build_review(location_id=location.id)
    db_session.add(review)
    await db_session.flush()

    service = GenerationService(db_session, provider=mock_llm_provider)
    response = await service.generate_for_review(review.id)

    assert response.status == ResponseStatus.pending_validation_client
    assert response.content.startswith("Merci pour votre avis")
    assert response.ai_status == 1
    assert review.status == ReviewStatus.awaiting_response


async def test_generate_routes_to_team_validation_in_team_mode(
    db_session: AsyncSession, mock_llm_provider: AsyncMock
) -> None:
    _client, _user, _settings, _sub, location, _cred = await create_full_client(
        db_session, validation_mode=ValidationMode.team
    )
    await _seed_prompt(db_session)
    review = build_review(location_id=location.id)
    db_session.add(review)
    await db_session.flush()

    service = GenerationService(db_session, provider=mock_llm_provider)
    response = await service.generate_for_review(review.id)

    assert response.status == ResponseStatus.pending_validation_team


async def test_generate_routes_refusal_to_team(
    db_session: AsyncSession, mock_llm_provider: AsyncMock
) -> None:
    """status=0 (refusal) must always go to team review."""
    _client, _user, _settings, _sub, location, _cred = await create_full_client(
        db_session, validation_mode=ValidationMode.suggestion
    )
    await _seed_prompt(db_session)
    review = build_review(location_id=location.id)
    db_session.add(review)
    await db_session.flush()

    mock_llm_provider.generate = AsyncMock(
        return_value=LLMResponse(
            status=0, content="", details="extreme_negative", model="claude-sonnet-4-6"
        )
    )
    service = GenerationService(db_session, provider=mock_llm_provider)
    response = await service.generate_for_review(review.id)
    assert response.status == ResponseStatus.pending_validation_team


async def test_generate_handles_llm_exception_as_team_review(
    db_session: AsyncSession, mock_llm_provider: AsyncMock
) -> None:
    _client, _user, _settings, _sub, location, _cred = await create_full_client(
        db_session, validation_mode=ValidationMode.suggestion
    )
    await _seed_prompt(db_session)
    review = build_review(location_id=location.id)
    db_session.add(review)
    await db_session.flush()

    mock_llm_provider.generate = AsyncMock(side_effect=RuntimeError("Claude down"))
    service = GenerationService(db_session, provider=mock_llm_provider)
    response = await service.generate_for_review(review.id)
    assert response.status == ResponseStatus.pending_validation_team
    assert response.ai_status == 0
    assert response.ai_details == "generation_error"


async def test_generate_raises_when_quota_exhausted(
    db_session: AsyncSession, mock_llm_provider: AsyncMock
) -> None:
    from tests.factories import build_quota_usage

    _client, _user, _settings, sub, location, _cred = await create_full_client(db_session)
    sub.monthly_response_quota = 1
    usage = build_quota_usage(client_id=location.client_id, count=1)
    db_session.add(usage)
    await _seed_prompt(db_session)
    review = build_review(location_id=location.id)
    db_session.add(review)
    await db_session.flush()

    service = GenerationService(db_session, provider=mock_llm_provider)
    with pytest.raises(QuotaExhaustedError):
        await service.generate_for_review(review.id)


async def test_generate_missing_review_raises(
    db_session: AsyncSession, mock_llm_provider: AsyncMock
) -> None:
    from uuid import uuid4

    service = GenerationService(db_session, provider=mock_llm_provider)
    with pytest.raises(ValueError, match="not found"):
        await service.generate_for_review(uuid4())
