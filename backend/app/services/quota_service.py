from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.quota_repository import QuotaRepository, current_year_month
from app.repositories.subscription_repository import SubscriptionRepository


class QuotaExhaustedError(Exception):
    pass


class QuotaService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.quotas = QuotaRepository(session)
        self.subscriptions = SubscriptionRepository(session)

    async def consume_or_raise(self, client_id: UUID) -> int:
        """Consume one quota unit. Raise QuotaExhaustedError if monthly cap reached."""
        subscription = await self.subscriptions.get_by_client(client_id)
        if subscription is None:
            raise RuntimeError(f"No subscription for client {client_id}")
        usage = await self.quotas.get_or_create(client_id, current_year_month())
        if usage.count >= subscription.monthly_response_quota:
            raise QuotaExhaustedError(
                f"Quota {subscription.monthly_response_quota} reached for client {client_id}"
            )
        return await self.quotas.increment(client_id)
