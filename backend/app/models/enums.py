import enum


class UserRole(enum.StrEnum):
    client = "client"
    admin = "admin"


class ClientStatus(enum.StrEnum):
    active = "active"
    paused = "paused"
    suspended = "suspended"


class SubscriptionTier(enum.StrEnum):
    starter = "starter"
    pro = "pro"
    business = "business"


class SubscriptionStatus(enum.StrEnum):
    trial = "trial"
    active = "active"
    past_due = "past_due"
    cancelled = "cancelled"
    expired = "expired"


class OAuthCredentialStatus(enum.StrEnum):
    active = "active"
    expiring = "expiring"
    expired = "expired"
    revoked = "revoked"


class LocationStatus(enum.StrEnum):
    active = "active"
    paused = "paused"


class ReviewStatus(enum.StrEnum):
    detected = "detected"
    filtering = "filtering"
    blocked_regex = "blocked_regex"
    requires_human_validation = "requires_human_validation"
    processing = "processing"
    awaiting_response = "awaiting_response"
    completed = "completed"


class ResponseStatus(enum.StrEnum):
    draft = "draft"
    pending_validation_client = "pending_validation_client"
    pending_validation_team = "pending_validation_team"
    awaiting_publication = "awaiting_publication"
    scheduled = "scheduled"
    publishing = "publishing"
    published = "published"
    failed = "failed"
    cancelled = "cancelled"
    superseded = "superseded"


class ResponseSource(enum.StrEnum):
    ai = "ai"
    manual_validator = "manual_validator"
    manual_client = "manual_client"


class PublishDelayRange(enum.StrEnum):
    range_1h_2h = "1h_2h"
    range_2h_5h = "2h_5h"
    range_5h_1d = "5h_1d"
    range_1d_2d = "1d_2d"
    range_2d_5d = "2d_5d"


class NoTextReviewPolicy(enum.StrEnum):
    ignore = "ignore"
    reply_4_5_only = "reply_4_5_only"
    reply_all = "reply_all"


class ValidationMode(enum.StrEnum):
    suggestion = "suggestion"
    team = "team"


class NotificationChannel(enum.StrEnum):
    email = "email"
    telegram = "telegram"
    sms = "sms"


class NotificationStatus(enum.StrEnum):
    pending = "pending"
    deferred = "deferred"
    sent = "sent"
    failed = "failed"
