from datetime import UTC, datetime
from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.google_business.adapter import GoogleBusinessAdapter
from app.integrations.google_business.client import GoogleBusinessClient
from app.integrations.google_business.exceptions import GoogleAuthError
from app.models.enums import OAuthCredentialStatus, ReviewStatus
from app.models.review import Review
from app.repositories.location_repository import LocationRepository
from app.repositories.oauth_repository import OAuthRepository
from app.repositories.review_repository import ReviewRepository


class PollingService:
    def __init__(
        self,
        session: AsyncSession,
        adapter: GoogleBusinessAdapter | None = None,
    ) -> None:
        self.session = session
        self.adapter: GoogleBusinessAdapter = adapter or GoogleBusinessClient()
        self.reviews = ReviewRepository(session)
        self.locations = LocationRepository(session)
        self.oauth = OAuthRepository(session)

    async def poll_client(self, client_id: UUID) -> list[UUID]:
        """Fetch new reviews for all locations of a client.

        Returns list of newly inserted review IDs. Existing reviews are skipped (dedup).
        Raises GoogleAuthError if OAuth credential is invalid (caller must handle).
        """
        credential = await self.oauth.get_by_client(client_id)
        if credential is None or credential.status != OAuthCredentialStatus.active:
            logger.warning(
                "Skipping polling for client {cid}: no active OAuth credential", cid=client_id
            )
            return []

        access_token = credential.access_token_encrypted
        new_review_ids: list[UUID] = []

        for location in await self.locations.list_by_client(client_id):
            try:
                page_token: str | None = None
                while True:
                    google_reviews, next_token = await self.adapter.list_reviews(
                        access_token,
                        f"accounts/{location.google_account_id}/locations/{location.google_location_id}",
                        page_token=page_token,
                    )
                    for gr in google_reviews:
                        existing = await self.reviews.get_by_google_id(gr.review_id)
                        if existing is not None:
                            continue
                        review = Review(
                            location_id=location.id,
                            google_review_id=gr.review_id,
                            reviewer_display_name=gr.reviewer_display_name,
                            reviewer_first_name=(
                                gr.reviewer_display_name.split()[0]
                                if gr.reviewer_display_name
                                else None
                            ),
                            rating=gr.rating,
                            comment=gr.comment,
                            posted_at=gr.create_time,
                            last_edited_at=gr.update_time,
                            fetched_at=datetime.now(UTC),
                            status=ReviewStatus.detected,
                        )
                        await self.reviews.add(review)
                        new_review_ids.append(review.id)
                    if not next_token:
                        break
                    page_token = next_token
            except GoogleAuthError:
                credential.status = OAuthCredentialStatus.revoked
                await self.session.commit()
                raise

        await self.session.commit()
        return new_review_ids
