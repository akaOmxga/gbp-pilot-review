from uuid import UUID

from sqlalchemy import CHAR, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, uuid7


class QuotaUsage(Base, CreatedAtMixin):
    __tablename__ = "quota_usage"
    __table_args__ = (UniqueConstraint("client_id", "year_month", name="uq_quota_client_month"),)

    id: Mapped[UUID] = mapped_column(default=uuid7, primary_key=True)
    client_id: Mapped[UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
    )
    year_month: Mapped[str] = mapped_column(CHAR(7), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_alert_threshold: Mapped[int | None] = mapped_column(Integer, nullable=True)
