from datetime import datetime, time
from uuid import UUID

from pydantic import BaseModel, EmailStr


class _BaseExport(BaseModel):
    model_config = {"from_attributes": True}


class UserExport(_BaseExport):
    id: UUID
    email: EmailStr
    role: str
    email_verified_at: datetime | None = None
    mfa_enabled: bool
    last_login_at: datetime | None = None
    client_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class ClientExport(_BaseExport):
    id: UUID
    business_name: str
    slug: str
    business_context: str
    tone_instructions: str
    status: str
    onboarding_completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ClientSettingsExport(_BaseExport):
    polling_frequency_minutes: int
    publish_delay_range: str
    publish_window_start: time
    publish_window_end: time
    publish_window_timezone: str
    language_override: str | None = None
    no_text_review_policy: str
    validation_mode: str
    digest_mode: bool
    digest_hour: int
    regex_blocklist: list[str]


class LocationExport(_BaseExport):
    id: UUID
    google_location_id: str
    name: str
    address: str | None = None
    primary_category: str | None = None
    status: str


class ReviewExport(_BaseExport):
    id: UUID
    location_id: UUID
    google_review_id: str
    reviewer_display_name: str | None = None
    rating: int
    comment: str | None = None
    language: str | None = None
    posted_at: datetime
    status: str


class ResponseExport(_BaseExport):
    id: UUID
    review_id: UUID
    version: int
    source: str
    content: str
    status: str
    scheduled_at: datetime | None = None
    published_at: datetime | None = None


class SubscriptionExport(_BaseExport):
    tier: str
    status: str
    trial_ends_at: datetime | None = None
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancelled_at: datetime | None = None
    monthly_response_quota: int


class NotificationPreferenceExport(_BaseExport):
    primary_channel: str
    email_address: str | None = None
    telegram_chat_id: str | None = None
    telegram_verified_at: datetime | None = None
    sms_phone: str | None = None


class UserDataExport(BaseModel):
    exported_at: datetime
    user: UserExport
    client: ClientExport | None = None
    client_settings: ClientSettingsExport | None = None
    locations: list[LocationExport] = []
    reviews: list[ReviewExport] = []
    responses: list[ResponseExport] = []
    subscription: SubscriptionExport | None = None
    notification_preference: NotificationPreferenceExport | None = None
