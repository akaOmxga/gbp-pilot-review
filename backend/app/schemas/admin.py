from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import (
    ClientStatus,
    OAuthCredentialStatus,
    SubscriptionStatus,
    SubscriptionTier,
)


class AdminClientListItem(BaseModel):
    id: UUID
    business_name: str
    slug: str
    status: ClientStatus
    created_at: datetime
    owner_email: str | None = None
    has_oauth: bool = False
    oauth_status: OAuthCredentialStatus | None = None
    pending_count: int = 0

    model_config = {"from_attributes": True}


class AdminClientDetail(BaseModel):
    id: UUID
    business_name: str
    slug: str
    status: ClientStatus
    business_context: str
    tone_instructions: str
    admin_notes: str | None = None
    onboarding_completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    owner_email: str | None = None
    subscription_tier: SubscriptionTier | None = None
    subscription_status: SubscriptionStatus | None = None
    oauth_status: OAuthCredentialStatus | None = None
    oauth_expires_at: datetime | None = None
    locations_count: int = 0

    reviews_total: int = 0
    responses_published_total: int = 0
    pending_validation: int = 0

    model_config = {"from_attributes": True}


class AdminClientNotesUpdate(BaseModel):
    admin_notes: str | None = Field(default=None, max_length=5000)


class AdminClientMetrics(BaseModel):
    client_id: UUID
    reviews_total: int
    reviews_30d: int
    responses_published_total: int
    responses_published_30d: int
    response_rate_30d: float
    last_review_at: datetime | None = None
    last_published_at: datetime | None = None


class AdminOAuthCredentialPublic(BaseModel):
    client_id: UUID
    business_name: str
    status: OAuthCredentialStatus
    expires_at: datetime
    last_refreshed_at: datetime | None = None
    last_check_at: datetime | None = None
    last_error: str | None = None


class AdminSystemMetrics(BaseModel):
    active_clients: int
    suspended_clients: int
    paused_clients: int
    responses_published_24h: int
    pending_validation: int
    dlq_depth: int
    oauth_alerts: int


class AdminValidationQueueItem(BaseModel):
    id: UUID
    review_id: UUID
    client_id: UUID
    client_business_name: str
    content: str
    status: str
    source: str
    ai_model: str | None = None
    created_at: datetime
    review_rating: int | None = None
    review_author: str | None = None
    review_comment: str | None = None
    review_posted_at: datetime | None = None


class AdminDeletePublishedRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class AdminPublishedDeletionPublic(BaseModel):
    id: int
    actor_user_id: UUID | None = None
    response_id: UUID | None = None
    review_id: UUID | None = None
    client_id: UUID | None = None
    reason: str | None = None
    created_at: datetime
