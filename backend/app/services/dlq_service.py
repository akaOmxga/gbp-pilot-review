import asyncio
from datetime import UTC, datetime
from typing import Any

from celery.signals import task_failure  # type: ignore[import-untyped]
from loguru import logger

from app.celery_app import celery_app
from app.database import get_sessionmaker
from app.models.dead_letter_job import DeadLetterJob


def _serialize_args(args: Any) -> list[Any]:
    try:
        return [str(a) for a in (args or [])]
    except Exception:
        return []


def _serialize_kwargs(kwargs: Any) -> dict[str, Any]:
    if not kwargs:
        return {}
    try:
        return {k: str(v) for k, v in kwargs.items()}
    except Exception:
        return {}


@task_failure.connect  # type: ignore[untyped-decorator]
def _on_task_failure(  # type: ignore[no-untyped-def]
    sender=None,
    task_id: str | None = None,
    exception: BaseException | None = None,
    args: Any = None,
    kwargs: Any = None,
    traceback: Any = None,
    einfo: Any = None,
    **_: Any,
) -> None:
    if sender is None:
        return
    task = sender
    request = getattr(task, "request", None)
    retries = getattr(request, "retries", 0) if request else 0
    max_retries = getattr(task, "max_retries", 0) or 0

    if retries < max_retries:
        return  # Will retry — not a dead letter yet.

    async def _persist() -> None:
        sm = get_sessionmaker()
        async with sm() as session:
            session.add(
                DeadLetterJob(
                    task_name=getattr(task, "name", "unknown"),
                    args=_serialize_args(args),
                    kwargs=_serialize_kwargs(kwargs),
                    last_error=str(exception)[:2000] if exception else "unknown",
                    traceback=str(einfo)[:5000] if einfo else None,
                    attempts=retries + 1,
                    failed_at=datetime.now(UTC),
                )
            )
            await session.commit()

    try:
        asyncio.run(_persist())
        logger.error(
            "Task {name} dead-lettered after {n} attempts: {err}",
            name=getattr(task, "name", "?"),
            n=retries + 1,
            err=exception,
        )
    except Exception:
        logger.exception("Failed to persist dead letter job")


def replay(dlq_id: int) -> None:
    """Re-enqueue a previously dead-lettered task."""

    async def _run() -> tuple[str, list[Any], dict[str, Any]] | None:
        sm = get_sessionmaker()
        async with sm() as session:
            from app.repositories.dead_letter_repository import DeadLetterRepository

            repo = DeadLetterRepository(session)
            job = await repo.get(dlq_id)
            if job is None:
                return None
            job.replayed_at = datetime.now(UTC)
            await session.commit()
            return job.task_name, list(job.args or []), dict(job.kwargs or {})

    info = asyncio.run(_run())
    if info is None:
        return
    name, args, kwargs = info
    celery_app.send_task(name, args=args, kwargs=kwargs)
