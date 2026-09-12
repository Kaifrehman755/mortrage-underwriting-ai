"""Underwriting decision ORM model (Reserved for Phase 1+)."""

from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class UnderwritingDecision(Base, TimestampMixin):
    """Database model representing final underwriting recommendations and human overrides."""

    __tablename__ = "underwriting_decisions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
