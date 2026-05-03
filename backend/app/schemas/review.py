from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ReviewPublic(BaseModel):
    id: UUID
    location_id: UUID
    google_review_id: str
    reviewer_display_name: str | None = None
    rating: int
    comment: str | None = None
    language: str | None = None
    posted_at: datetime
    status: str
    block_reason: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
