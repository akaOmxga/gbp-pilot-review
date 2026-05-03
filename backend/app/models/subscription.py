from datetime import datetime
from uuid import UUID

from sqlalchemy import TIMESTAMP, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuid7
from app.models.enums import SubscriptionStatus, SubscriptionTier


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    id: Mapped[UUID] = mapped_column(default=uuid7, primary_key=True)
    client_id: Mapped[UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    tier: Mapped[SubscriptionTier] = mapped_column(
        ENUM(SubscriptionTier, name="subscription_tier", create_type=True), nullable=False
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        ENUM(SubscriptionStatus, name="subscription_status", create_type=True), nullable=False
    )
    lemonsqueezy_subscription_id: Mapped[str | None] = mapped_column(
        String, unique=True, nullable=True
    )
    lemonsqueezy_customer_id: Mapped[str | None] = mapped_column(String, nullable=True)
    trial_ends_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    current_period_start: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    monthly_response_quota: Mapped[int] = mapped_column(Integer, nullable=False)
