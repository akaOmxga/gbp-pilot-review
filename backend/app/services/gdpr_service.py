from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.response import Response as ResponseModel
from app.models.review import Review
from app.models.user import User
from app.repositories.client_settings_repository import ClientSettingsRepository
from app.repositories.location_repository import LocationRepository
from app.repositories.notification_repository import NotificationPreferenceRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.schemas.export import (
    ClientExport,
    ClientSettingsExport,
    LocationExport,
    NotificationPreferenceExport,
    ResponseExport,
    ReviewExport,
    SubscriptionExport,
    UserDataExport,
    UserExport,
)


class GDPRService:
    """RGPD Art. 15 — droit d'accès: assemble the user's data on demand."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def export_user_data(self, user: User) -> UserDataExport:
        client_id: UUID | None = user.client_id
        client_export: ClientExport | None = None
        settings_export: ClientSettingsExport | None = None
        location_exports: list[LocationExport] = []
        review_exports: list[ReviewExport] = []
        response_exports: list[ResponseExport] = []
        subscription_export: SubscriptionExport | None = None
        notif_export: NotificationPreferenceExport | None = None

        if client_id is not None:
            client = await self.session.get(Client, client_id)
            if client is not None:
                client_export = ClientExport.model_validate(client)

            settings = await ClientSettingsRepository(self.session).get_by_client(client_id)
            if settings is not None:
                settings_export = ClientSettingsExport.model_validate(settings)

            locations = await LocationRepository(self.session).list_by_client(client_id)
            location_exports = [LocationExport.model_validate(loc) for loc in locations]

            if locations:
                location_ids = [loc.id for loc in locations]
                review_stmt = select(Review).where(Review.location_id.in_(location_ids))
                reviews = (await self.session.scalars(review_stmt)).all()
                review_exports = [ReviewExport.model_validate(r) for r in reviews]

                if reviews:
                    review_ids = [r.id for r in reviews]
                    response_stmt = select(ResponseModel).where(
                        ResponseModel.review_id.in_(review_ids)
                    )
                    responses = (await self.session.scalars(response_stmt)).all()
                    response_exports = [ResponseExport.model_validate(r) for r in responses]

            subscription = await SubscriptionRepository(self.session).get_by_client(client_id)
            if subscription is not None:
                subscription_export = SubscriptionExport.model_validate(subscription)

            notif = await NotificationPreferenceRepository(self.session).get_by_client(client_id)
            if notif is not None:
                notif_export = NotificationPreferenceExport.model_validate(notif)

        return UserDataExport(
            exported_at=datetime.now(UTC),
            user=UserExport.model_validate(user),
            client=client_export,
            client_settings=settings_export,
            locations=location_exports,
            reviews=review_exports,
            responses=response_exports,
            subscription=subscription_export,
            notification_preference=notif_export,
        )
