from sqlalchemy import select

from app.models.prompt_version import PromptVersion
from app.repositories.base import CRUDRepository


class PromptVersionRepository(CRUDRepository[PromptVersion]):
    model = PromptVersion

    async def get_active(self) -> PromptVersion | None:
        stmt = select(PromptVersion).where(PromptVersion.is_active.is_(True))
        return (await self.session.scalars(stmt)).first()
