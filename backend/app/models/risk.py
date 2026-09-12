"""Risk assessment ORM model (Reserved for Phase 1+)."""

from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class RiskAssessment(Base, TimestampMixin):
    """Database model representing computed risk metrics."""

    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
