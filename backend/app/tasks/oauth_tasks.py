from datetime import UTC, datetime, timedelta

from loguru import logger

from app.celery_app import celery_app


@celery_app.task(name="app.tasks.oauth_tasks.refresh_expiring_tokens", bind=True)  # type: ignore[untyped-decorator]
def refresh_expiring_tokens(self) -> dict[str, int]:  # type: ignore[no-untyped-def]
    """Beat job: proactively refresh OAuth tokens expiring within 60 minutes."""
    import asyncio

    from app.database import get_sessionmaker
    from app.integrations.google_business.exceptions import GoogleAuthError
    from app.repositories.oauth_repository import OAuthRepository
    from app.services.oauth_service import OAuthService

    async def _run() -> dict[str, int]:
        sm = get_sessionmaker()
        async with sm() as session:
            repo = OAuthRepository(session)
            cutoff = datetime.now(UTC) + timedelta(minutes=60)
            credentials = await repo.list_expiring_before(cutoff)
            refreshed = 0
            revoked = 0
            for credential in credentials:
                service = OAuthService(session)
                try:
                    await service.refresh(credential)
                    refreshed += 1
                except GoogleAuthError:
                    revoked += 1
                    logger.warning(
                        "OAuth refresh failed (revoked) for client {client_id}",
                        client_id=credential.client_id,
                    )
            return {"refreshed": refreshed, "revoked": revoked}

    return asyncio.run(_run())
