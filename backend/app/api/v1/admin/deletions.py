from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser
from app.database import SessionDep
from app.models.client import Client
from app.models.enums import UserRole
from app.models.user import User
from app.services.audit_service import audit

router = APIRouter(prefix="/admin/deletions", tags=["admin"])


def _ensure_admin(user) -> None:  # type: ignore[no-untyped-def]
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


@router.post("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_user(
    user_id: UUID, session: SessionDep, user: CurrentUser
) -> None:
    _ensure_admin(user)
    target = await session.get(User, user_id)
    if target is None:
        raise HTTPException(404)
    target.deleted_at = datetime.now(UTC)
    await audit(
        session,
        actor_user_id=user.id,
        action="user.soft_delete",
        target_type="user",
        target_id=target.id,
    )
    await session.commit()


@router.post("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_client(
    client_id: UUID, session: SessionDep, user: CurrentUser
) -> None:
    _ensure_admin(user)
    target = await session.get(Client, client_id)
    if target is None:
        raise HTTPException(404)
    target.deleted_at = datetime.now(UTC)
    await audit(
        session,
        actor_user_id=user.id,
        action="client.soft_delete",
        target_type="client",
        target_id=target.id,
    )
    await session.commit()
