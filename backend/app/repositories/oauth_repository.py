from datetime import datetime
from uuid import UUID

from sqlalchemy import select

from app.models.oauth_credential import OAuthCredential
from app.repositories.base import CRUDRepository


class OAuthRepository(CRUDRepository[OAuthCredential]):
    model = OAuthCredential

    async def get_by_client(self, client_id: UUID) -> OAuthCredential | None:
        stmt = select(OAuthCredential).where(OAuthCredential.client_id == client_id)
        return (await self.session.scalars(stmt)).first()

    async def list_expiring_before(self, when: datetime) -> list[OAuthCredential]:
        stmt = (
            select(OAuthCredential)
            .where(OAuthCredential.expires_at <= when)
            .where(OAuthCredential.status.in_(("active", "expiring")))
        )
        return list((await self.session.scalars(stmt)).all())
