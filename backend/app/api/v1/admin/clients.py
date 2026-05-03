from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentUser
from app.database import SessionDep
from app.models.client import Client
from app.models.enums import ClientStatus, UserRole
from app.services.audit_service import audit

router = APIRouter(prefix="/admin/clients", tags=["admin"])


class ClientPublic(BaseModel):
    id: UUID
    business_name: str
    slug: str
    status: str

    model_config = {"from_attributes": True}


def _ensure_admin(user) -> None:  # type: ignore[no-untyped-def]
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


@router.get("", response_model=list[ClientPublic])
async def list_clients(
    session: SessionDep,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[ClientPublic]:
    _ensure_admin(user)
    stmt = select(Client).where(Client.deleted_at.is_(None)).limit(limit)
    rows = (await session.scalars(stmt)).all()
    return [ClientPublic.model_validate(r) for r in rows]


@router.post("/{client_id}/suspend", response_model=ClientPublic)
async def suspend(
    client_id: UUID, session: SessionDep, user: CurrentUser
) -> ClientPublic:
    _ensure_admin(user)
    client = await session.get(Client, client_id)
    if client is None:
        raise HTTPException(404)
    client.status = ClientStatus.suspended
    await audit(
        session,
        actor_user_id=user.id,
        action="client.suspend",
        target_type="client",
        target_id=client.id,
    )
    await session.commit()
    return ClientPublic.model_validate(client)


@router.post("/{client_id}/reactivate", response_model=ClientPublic)
async def reactivate(
    client_id: UUID, session: SessionDep, user: CurrentUser
) -> ClientPublic:
    _ensure_admin(user)
    client = await session.get(Client, client_id)
    if client is None:
        raise HTTPException(404)
    client.status = ClientStatus.active
    await audit(
        session,
        actor_user_id=user.id,
        action="client.reactivate",
        target_type="client",
        target_id=client.id,
    )
    await session.commit()
    return ClientPublic.model_validate(client)
