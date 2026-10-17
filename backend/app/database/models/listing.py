"""SQLAlchemy ORM model for Property Listings (Asking Prices).

Enforces GEMINI.md Section 4.4:
- Invariant: Stores asking-price evidence separately from verified sale transactions.
- Never conflates listing prices with completed sales.
"""

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class PropertyListing(Base, TimestampMixin):
    """Stores asking-price listings separate from actual transactions."""

    __tablename__ = "property_listings"

    listing_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    property_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("property_records.property_id"), nullable=True, index=True
    )
    source_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("data_sources.source_id"), nullable=False, index=True
    )
    source_listing_id: Mapped[str] = mapped_column(String(100), nullable=False)
    asking_price_raw: Mapped[float] = mapped_column(Float, nullable=False)
    asking_price_inr: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    listing_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    listing_status: Mapped[str] = mapped_column(String(30), nullable=False, default="active", index=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_record_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "source_id", "source_listing_id", name="uq_listing_source_listing_id"
        ),
    )
