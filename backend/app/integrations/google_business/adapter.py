from collections.abc import Sequence
from typing import Protocol

from app.integrations.google_business.schemas import (
    GoogleLocation,
    GoogleReview,
    GoogleReviewReplyResult,
    GoogleTokenResponse,
)


class GoogleBusinessAdapter(Protocol):
    """Contract for Google Business Profile operations.

    Implementations: real httpx client (production) or in-memory fake (tests).
    """

    async def exchange_code(self, code: str, redirect_uri: str) -> GoogleTokenResponse: ...

    async def refresh_token(self, refresh_token: str) -> GoogleTokenResponse: ...

    async def revoke_token(self, token: str) -> None: ...

    async def list_locations(self, access_token: str) -> Sequence[GoogleLocation]: ...

    async def list_reviews(
        self, access_token: str, location_name: str, page_token: str | None = None
    ) -> tuple[Sequence[GoogleReview], str | None]: ...

    async def reply_to_review(
        self, access_token: str, review_name: str, comment: str
    ) -> GoogleReviewReplyResult: ...

    async def delete_reply(self, access_token: str, review_name: str) -> None: ...
