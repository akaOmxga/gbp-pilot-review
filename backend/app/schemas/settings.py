from datetime import time

from pydantic import BaseModel, Field

from app.models.enums import (
    NoTextReviewPolicy,
    PublishDelayRange,
    ValidationMode,
)


class ClientSettingsPublic(BaseModel):
    polling_frequency_minutes: int
    publish_delay_range: PublishDelayRange
    publish_window_start: time
    publish_window_end: time
    publish_window_timezone: str
    language_override: str | None = None
    no_text_review_policy: NoTextReviewPolicy
    validation_mode: ValidationMode
    digest_mode: bool
    digest_hour: int
    regex_blocklist: list[str]

    model_config = {"from_attributes": True}


class ClientSettingsUpdate(BaseModel):
    polling_frequency_minutes: int | None = Field(default=None, ge=15, le=1440 * 7)
    publish_delay_range: PublishDelayRange | None = None
    publish_window_start: time | None = None
    publish_window_end: time | None = None
    publish_window_timezone: str | None = None
    language_override: str | None = Field(default=None, min_length=2, max_length=2)
    no_text_review_policy: NoTextReviewPolicy | None = None
    validation_mode: ValidationMode | None = None
    digest_mode: bool | None = None
    digest_hour: int | None = Field(default=None, ge=0, le=23)
    regex_blocklist: list[str] | None = None
