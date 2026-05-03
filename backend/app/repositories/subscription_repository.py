from uuid import UUID

from sqlalchemy import select

from app.models.subscription import Subscription
from app.repositories.base import CRUDRepository


class SubscriptionRepository(CRUDRepository[Subscription]):
    model = Subscription

    async def get_by_client(self, client_id: UUID) -> Subscription | None:
        stmt = select(Subscription).where(Subscription.client_id == client_id)
        return (await self.session.scalars(stmt)).first()
