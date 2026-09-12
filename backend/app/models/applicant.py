"""Applicant ORM model (Reserved for Phase 1+)."""

from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class Applicant(Base, TimestampMixin):
    """Database model representing an applicant or co-borrower."""

    __tablename__ = "applicants"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
