from uuid import UUID

from sqlalchemy import select

from app.models.client_settings import ClientSettings
from app.repositories.base import CRUDRepository


class ClientSettingsRepository(CRUDRepository[ClientSettings]):
    model = ClientSettings

    async def get_by_client(self, client_id: UUID) -> ClientSettings | None:
        stmt = select(ClientSettings).where(ClientSettings.client_id == client_id)
        return (await self.session.scalars(stmt)).first()
