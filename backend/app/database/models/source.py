"""SQLAlchemy ORM model for Data Sources and Provenance.

Enforces GEMINI.md Section 4.1:
- Provider identity, licensing scope, and approval gate status.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class DataSource(Base, TimestampMixin):
    """Stores data provider identity, access method, and approval status."""

    __tablename__ = "data_sources"

    source_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    source_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    official_url: Mapped[str] = mapped_column(Text, nullable=False)
    access_method: Mapped[str] = mapped_column(String(50), nullable=False)
    license_scope: Mapped[str] = mapped_column(Text, nullable=False)
    approval_status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending_review", index=True)
    terms_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_successful_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
