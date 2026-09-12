"""Credit report ORM model (Reserved for Phase 1+)."""

from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class CreditProfile(Base, TimestampMixin):
    """Database model representing borrower credit report data."""

    __tablename__ = "credit_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
