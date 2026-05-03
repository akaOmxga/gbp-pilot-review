from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def audit(
    session: AsyncSession,
    *,
    actor_user_id: UUID | None,
    action: str,
    target_type: str,
    target_id: UUID | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    log = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata_=metadata or {},
    )
    session.add(log)
    await session.flush()
    return log
