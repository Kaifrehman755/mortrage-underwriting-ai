"""Document ORM model (Reserved for Phase 1+)."""

from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class Document(Base, TimestampMixin):
    """Database model representing uploaded borrower documents."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
