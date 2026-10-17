"""SQLAlchemy ORM model for Administrative Reference Rates.

Enforces GEMINI.md Section 4.5:
- Stores official circle rates, guidance values, ready-reckoner rates.
- Invariant: Never used as if it were a sale transaction table.
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


class ReferenceRate(Base, TimestampMixin):
    """Stores official state administrative reference rates (guidance values / circle rates)."""

    __tablename__ = "reference_rates"

    rate_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    source_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("data_sources.source_id"), nullable=False, index=True
    )
    state_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    locality: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    property_category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    rate_raw: Mapped[float] = mapped_column(Float, nullable=False)
    rate_unit_raw: Mapped[str] = mapped_column(String(30), nullable=False)
    # F-17/F-12: the basis is INR per square FOOT (never per square metre). The contract, ORM
    # attribute and physical DB column all use the unambiguous name `rate_inr_per_sqft`
    # (renamed from the historical `rate_inr_normalized` under the ratified F-12 migration).
    rate_inr_per_sqft: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        index=True,
        comment="Normalized reference rate in INR per square FOOT (not per square metre)",
    )

    effective_from: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    published_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_record_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "state_code",
            "district",
            "locality",
            "property_category",
            "effective_from",
            name="uq_reference_rate_state_dist_loc_cat_date",
        ),
    )
