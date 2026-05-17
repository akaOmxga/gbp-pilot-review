"""Unit tests for DLQ service replay flow."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.dead_letter_repository import DeadLetterRepository
from tests.factories import build_dead_letter_job

pytestmark = pytest.mark.integration


async def test_dlq_repository_lists_unreplayed(db_session: AsyncSession) -> None:
    from datetime import UTC, datetime

    job_a = build_dead_letter_job(task_name="a", last_error="boom A")
    job_b = build_dead_letter_job(task_name="b", last_error="boom B")
    job_b.replayed_at = datetime.now(UTC)
    db_session.add_all([job_a, job_b])
    await db_session.flush()

    repo = DeadLetterRepository(db_session)
    pending = await repo.list_unreplayed()
    assert len(pending) == 1
    assert pending[0].task_name == "a"


async def test_dlq_job_persists_args_kwargs(db_session: AsyncSession) -> None:
    job = build_dead_letter_job(args=["1", "2"], kwargs={"k": "v"})
    db_session.add(job)
    await db_session.flush()
    await db_session.refresh(job)
    assert job.args == ["1", "2"]
    assert job.kwargs == {"k": "v"}
