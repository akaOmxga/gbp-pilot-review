from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base


class CRUDRepository[T: Base]:
    model: type[T]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, id_: UUID | int) -> T | None:
        return await self.session.get(self.model, id_)

    async def list(self, *, limit: int = 100, offset: int = 0) -> Sequence[T]:
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.scalars(stmt)
        return result.all()

    async def add(self, instance: T) -> T:
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def delete(self, instance: T) -> None:
        await self.session.delete(instance)
        await self.session.flush()

    async def update(self, instance: T, **fields: Any) -> T:
        for key, value in fields.items():
            setattr(instance, key, value)
        await self.session.flush()
        return instance
