from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import CurrentUser
from app.database import SessionDep
from app.models.enums import ResponseStatus, UserRole
from app.models.response import Response
from app.schemas.response import ResponsePublic

router = APIRouter(prefix="/admin/validation-queue", tags=["admin"])


@router.get("", response_model=list[ResponsePublic])
async def queue(
    session: SessionDep,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[ResponsePublic]:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    stmt = (
        select(Response)
        .where(Response.status == ResponseStatus.pending_validation_team)
        .order_by(Response.created_at.asc())
        .limit(limit)
    )
    rows = (await session.scalars(stmt)).all()
    return [ResponsePublic.model_validate(r) for r in rows]
