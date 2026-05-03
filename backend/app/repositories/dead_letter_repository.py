from collections.abc import Sequence

from sqlalchemy import select

from app.models.dead_letter_job import DeadLetterJob
from app.repositories.base import CRUDRepository


class DeadLetterRepository(CRUDRepository[DeadLetterJob]):
    model = DeadLetterJob

    async def list_unreplayed(self, limit: int = 100) -> Sequence[DeadLetterJob]:
        stmt = (
            select(DeadLetterJob)
            .where(DeadLetterJob.replayed_at.is_(None))
            .order_by(DeadLetterJob.failed_at.desc())
            .limit(limit)
        )
        return (await self.session.scalars(stmt)).all()
