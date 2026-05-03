from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class GoogleTokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    expires_in: int
    scope: str
    token_type: Literal["Bearer"] = "Bearer"


class GoogleLocation(BaseModel):
    name: str  # full resource name e.g. "accounts/123/locations/456"
    title: str
    primary_category: str | None = None
    address_lines: list[str] = Field(default_factory=list)


class GoogleReview(BaseModel):
    name: str  # full resource name including review id
    review_id: str
    reviewer_display_name: str | None = None
    rating: int
    comment: str | None = None
    create_time: datetime
    update_time: datetime | None = None


class GoogleReviewReplyResult(BaseModel):
    comment: str
    update_time: datetime
