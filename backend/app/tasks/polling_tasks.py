import asyncio
from uuid import UUID

from loguru import logger
from sqlalchemy import select

from app.celery_app import celery_app


@celery_app.task(name="app.tasks.polling_tasks.dispatch_pollings")  # type: ignore[untyped-decorator]
def dispatch_pollings() -> int:
    """Beat job: enqueue per-client polling tasks for all eligible clients."""
    from app.database import get_sessionmaker
    from app.models.client import Client
    from app.models.enums import ClientStatus

    async def _run() -> list[UUID]:
        sm = get_sessionmaker()
        async with sm() as session:
            stmt = select(Client.id).where(
                Client.status == ClientStatus.active, Client.deleted_at.is_(None)
            )
            return list((await session.scalars(stmt)).all())

    client_ids = asyncio.run(_run())
    for index, client_id in enumerate(client_ids):
        # Stagger by index seconds to avoid thundering herd against Google API.
        poll_client_reviews.apply_async(args=[str(client_id)], countdown=index)
    return len(client_ids)


@celery_app.task(  # type: ignore[untyped-decorator]
    name="app.tasks.polling_tasks.poll_client_reviews",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=1800,
    max_retries=3,
)
def poll_client_reviews(self, client_id: str) -> int:  # type: ignore[no-untyped-def]
    from app.database import get_sessionmaker
    from app.integrations.google_business.exceptions import GoogleAuthError
    from app.services.polling_service import PollingService

    async def _run() -> int:
        sm = get_sessionmaker()
        async with sm() as session:
            service = PollingService(session)
            try:
                new_ids = await service.poll_client(UUID(client_id))
            except GoogleAuthError:
                logger.warning("OAuth revoked for client {cid} during polling", cid=client_id)
                return 0
            for rid in new_ids:
                process_review_task.apply_async(args=[str(rid)])
            return len(new_ids)

    return asyncio.run(_run())


@celery_app.task(  # type: ignore[untyped-decorator]
    name="app.tasks.polling_tasks.process_review_task",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def process_review_task(self, review_id: str) -> str:  # type: ignore[no-untyped-def]
    """Hands the review off to the filtering pipeline (PR 6)."""
    from app.database import get_sessionmaker
    from app.services.filtering_service import FilteringService

    async def _run() -> str:
        sm = get_sessionmaker()
        async with sm() as session:
            service = FilteringService(session)
            decision = await service.decide(UUID(review_id))
            return decision.name

    return asyncio.run(_run())
