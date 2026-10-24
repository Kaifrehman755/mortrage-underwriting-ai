"""SQLAlchemy ORM model for Property Transactions.

Enforces GEMINI.md Section 4.3:
- Stores individual sale or transfer consideration.
- Invariant: Never treats registration fees or circle rates as sale prices.
- Unique constraint on (source_id, source_transaction_id).
"""

from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
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


class PropertyTransaction(Base, TimestampMixin):
    """Stores verified or reported sale consideration evidence."""

    __tablename__ = "property_transactions"

    transaction_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    property_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("property_records.property_id"), nullable=True, index=True
    )
    source_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("data_sources.source_id"), nullable=False, index=True
    )
    source_transaction_id: Mapped[str] = mapped_column(String(100), nullable=False)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    transaction_price_raw: Mapped[float] = mapped_column(Float, nullable=False)
    transaction_price_unit_raw: Mapped[str] = mapped_column(String(30), nullable=False)
    transaction_price_inr: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)

    price_type: Mapped[str] = mapped_column(String(50), nullable=False, default="unknown", index=True)
    transaction_verification_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="unverified", index=True
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_record_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "source_id", "source_transaction_id", name="uq_transaction_source_tx_id"
        ),
    )
