from datetime import datetime
from uuid import UUID

from sqlalchemy import TIMESTAMP, ForeignKey, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuid7
from app.models.enums import NotificationChannel


class NotificationPreference(Base, TimestampMixin):
    __tablename__ = "notification_preferences"

    id: Mapped[UUID] = mapped_column(default=uuid7, primary_key=True)
    client_id: Mapped[UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    primary_channel: Mapped[NotificationChannel] = mapped_column(
        ENUM(NotificationChannel, name="notification_channel", create_type=True),
        nullable=False,
        default=NotificationChannel.email,
    )
    email_address: Mapped[str | None] = mapped_column(String, nullable=True)
    telegram_chat_id: Mapped[str | None] = mapped_column(String, nullable=True)
    telegram_verified_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    sms_phone: Mapped[str | None] = mapped_column(String, nullable=True)
