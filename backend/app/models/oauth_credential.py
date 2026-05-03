from datetime import datetime
from uuid import UUID

from sqlalchemy import TIMESTAMP, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, ENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuid7
from app.models.enums import OAuthCredentialStatus
from app.security.encryption import EncryptedString


class OAuthCredential(Base, TimestampMixin):
    __tablename__ = "oauth_credentials"

    id: Mapped[UUID] = mapped_column(default=uuid7, primary_key=True)
    client_id: Mapped[UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    access_token_encrypted: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    refresh_token_encrypted: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    scopes: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    google_account_id: Mapped[str | None] = mapped_column(String, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    status: Mapped[OAuthCredentialStatus] = mapped_column(
        ENUM(OAuthCredentialStatus, name="oauth_credential_status", create_type=True),
        nullable=False,
        default=OAuthCredentialStatus.active,
    )
    last_refreshed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    last_check_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
