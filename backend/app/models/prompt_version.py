from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, uuid7


class PromptVersion(Base, CreatedAtMixin):
    __tablename__ = "prompt_versions"

    id: Mapped[UUID] = mapped_column(default=uuid7, primary_key=True)
    version: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    user_prompt_template: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    temperature: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, default=Decimal("0.70")
    )
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=600)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
