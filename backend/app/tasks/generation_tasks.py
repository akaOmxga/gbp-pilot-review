import asyncio
from uuid import UUID

from app.celery_app import celery_app


@celery_app.task(  # type: ignore[untyped-decorator]
    name="app.tasks.generation_tasks.generate_response",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=2,
)
def generate_response(self, review_id: str) -> str:  # type: ignore[no-untyped-def]
    from app.database import get_sessionmaker
    from app.services.generation_service import GenerationService
    from app.services.quota_service import QuotaExhaustedError

    async def _run() -> str:
        sm = get_sessionmaker()
        async with sm() as session:
            service = GenerationService(session)
            try:
                response = await service.generate_for_review(UUID(review_id))
            except QuotaExhaustedError:
                return "quota_exhausted"
            return str(response.id)

    return asyncio.run(_run())
