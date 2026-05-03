import asyncio
from uuid import UUID

from app.celery_app import celery_app


@celery_app.task(name="app.tasks.publication_tasks.dispatch_due_publications")  # type: ignore[untyped-decorator]
def dispatch_due_publications() -> int:
    """Beat job: every 1min, find scheduled responses past undo deadline and enqueue publish."""
    from app.database import get_sessionmaker
    from app.repositories.response_repository import ResponseRepository

    async def _run() -> list[UUID]:
        sm = get_sessionmaker()
        async with sm() as session:
            repo = ResponseRepository(session)
            due = await repo.list_due_publications(limit=100)
            ids = [r.id for r in due]
            await session.commit()
            return ids

    ids = asyncio.run(_run())
    for response_id in ids:
        publish_response.apply_async(args=[str(response_id)])
    return len(ids)


@celery_app.task(  # type: ignore[untyped-decorator]
    name="app.tasks.publication_tasks.publish_response",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=1800,
    max_retries=3,
)
def publish_response(self, response_id: str) -> str:  # type: ignore[no-untyped-def]
    from app.database import get_sessionmaker
    from app.repositories.response_repository import ResponseRepository
    from app.services.publication_service import PublicationService

    async def _run() -> str:
        sm = get_sessionmaker()
        async with sm() as session:
            repo = ResponseRepository(session)
            response = await repo.get(UUID(response_id))
            if response is None:
                return "missing"
            service = PublicationService(session)
            updated = await service.publish_now(response)
            return updated.status.value

    return asyncio.run(_run())
