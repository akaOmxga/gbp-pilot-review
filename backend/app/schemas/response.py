from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ResponsePublic(BaseModel):
    id: UUID
    review_id: UUID
    version: int
    is_active: bool
    source: str
    content: str
    status: str
    ai_status: int | None = None
    ai_details: str | None = None
    ai_model: str | None = None
    scheduled_at: datetime | None = None
    undo_deadline_at: datetime | None = None
    published_at: datetime | None = None
    failure_reason: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ResponseUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
