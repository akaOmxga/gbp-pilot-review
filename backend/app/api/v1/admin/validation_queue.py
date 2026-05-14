from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import CurrentUser
from app.database import SessionDep
from app.models.client import Client
from app.models.enums import ResponseStatus, UserRole
from app.models.location import Location
from app.models.response import Response
from app.models.review import Review
from app.schemas.admin import AdminValidationQueueItem

router = APIRouter(prefix="/admin/validation-queue", tags=["admin"])


@router.get("", response_model=list[AdminValidationQueueItem])
async def queue(
    session: SessionDep,
    user: CurrentUser,
    client_id: Annotated[UUID | None, Query()] = None,
    order: Annotated[Literal["oldest", "newest"], Query()] = "oldest",
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AdminValidationQueueItem]:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    stmt = (
        select(Response, Review, Client)
        .join(Review, Review.id == Response.review_id)
        .join(Location, Location.id == Review.location_id)
        .join(Client, Client.id == Location.client_id)
        .where(
            Response.status.in_(
                [
                    ResponseStatus.pending_validation_client,
                    ResponseStatus.pending_validation_team,
                ]
            ),
            Response.deleted_at.is_(None),
            Client.deleted_at.is_(None),
        )
    )
    if client_id is not None:
        stmt = stmt.where(Client.id == client_id)

    ordering = Response.created_at.asc() if order == "oldest" else Response.created_at.desc()
    stmt = stmt.order_by(ordering).limit(limit).offset(offset)

    rows = (await session.execute(stmt)).all()
    return [
        AdminValidationQueueItem(
            id=resp.id,
            review_id=resp.review_id,
            client_id=client.id,
            client_business_name=client.business_name,
            content=resp.content,
            status=resp.status.value,
            source=resp.source.value,
            ai_model=resp.ai_model,
            created_at=resp.created_at,
            review_rating=review.rating,
            review_author=review.reviewer_display_name,
            review_comment=review.comment,
            review_posted_at=review.posted_at,
        )
        for resp, review, client in rows
    ]
