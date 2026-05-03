from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select

from app.models.location import Location
from app.repositories.base import CRUDRepository


class LocationRepository(CRUDRepository[Location]):
    model = Location

    async def list_by_client(self, client_id: UUID) -> Sequence[Location]:
        stmt = select(Location).where(Location.client_id == client_id)
        return (await self.session.scalars(stmt)).all()

    async def get_by_google_id(self, google_location_id: str) -> Location | None:
        stmt = select(Location).where(Location.google_location_id == google_location_id)
        return (await self.session.scalars(stmt)).first()
