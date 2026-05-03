from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select

from app.models.enums import ResponseStatus
from app.models.response import Response
from app.repositories.base import CRUDRepository


class ResponseRepository(CRUDRepository[Response]):
    model = Response

    async def get_active_for_review(self, review_id: UUID) -> Response | None:
        stmt = (
            select(Response)
            .where(Response.review_id == review_id, Response.is_active.is_(True))
            .order_by(Response.version.desc())
        )
        return (await self.session.scalars(stmt)).first()

    async def list_due_publications(self, *, limit: int = 50) -> Sequence[Response]:
        from datetime import UTC, datetime

        stmt = (
            select(Response)
            .where(
                Response.status == ResponseStatus.scheduled,
                Response.scheduled_at <= datetime.now(UTC),
            )
            .order_by(Response.scheduled_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return (await self.session.scalars(stmt)).all()
