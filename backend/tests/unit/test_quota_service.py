"""Unit tests for QuotaService."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.quota_repository import current_year_month
from app.services.quota_service import QuotaExhaustedError, QuotaService
from tests.factories import build_quota_usage, create_full_client

pytestmark = pytest.mark.integration


async def test_consume_or_raise_increments_count(db_session: AsyncSession) -> None:
    _client, _user, _settings, sub, _location, _cred = await create_full_client(db_session)
    sub.monthly_response_quota = 10

    service = QuotaService(db_session)
    new_count = await service.consume_or_raise(sub.client_id)
    assert new_count == 1


async def test_consume_or_raise_blocks_at_cap(db_session: AsyncSession) -> None:
    _client, _user, _settings, sub, _location, _cred = await create_full_client(db_session)
    sub.monthly_response_quota = 2
    db_session.add(build_quota_usage(client_id=sub.client_id, count=2))
    await db_session.flush()

    service = QuotaService(db_session)
    with pytest.raises(QuotaExhaustedError):
        await service.consume_or_raise(sub.client_id)


async def test_get_or_create_idempotent(db_session: AsyncSession) -> None:
    from app.repositories.quota_repository import QuotaRepository

    _client, _user, _settings, _sub, _location, _cred = await create_full_client(db_session)
    repo = QuotaRepository(db_session)
    ym = current_year_month()
    a = await repo.get_or_create(_client.id, ym)
    b = await repo.get_or_create(_client.id, ym)
    assert a.id == b.id
