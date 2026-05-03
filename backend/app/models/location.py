from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, uuid7
from app.models.enums import LocationStatus


class Location(Base, TimestampMixin):
    __tablename__ = "locations"

    id: Mapped[UUID] = mapped_column(default=uuid7, primary_key=True)
    client_id: Mapped[UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
    )
    google_account_id: Mapped[str] = mapped_column(String, nullable=False)
    google_location_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_category: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[LocationStatus] = mapped_column(
        ENUM(LocationStatus, name="location_status", create_type=True),
        nullable=False,
        default=LocationStatus.active,
    )
