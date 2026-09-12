"""Application ORM model (Reserved for Phase 1+)."""

from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class Application(Base, TimestampMixin):
    """Database model representing a mortgage application."""

    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
