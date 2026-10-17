"""SQLAlchemy ORM model for official circle rates (guideline values)."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class CircleRate(Base, TimestampMixin):
    """Official circle rate / guideline value for a locality.

    One row per (state, district, zone_tehsil, locality, property_type, effective_year).
    rate_per_sqm is the government-notified minimum registration value per square metre.
    """

    __tablename__ = "circle_rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    zone_tehsil: Mapped[str] = mapped_column(String(100), nullable=False)
    locality: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    property_type: Mapped[str] = mapped_column(String(50), nullable=False)
    rate_per_sqm: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Government-notified circle rate in INR per SQUARE METRE (F-17 unit basis)",
    )
    effective_year: Mapped[int] = mapped_column(Integer, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "state",
            "district",
            "zone_tehsil",
            "locality",
            "property_type",
            "effective_year",
            name="uq_circle_rate_state_district_zone_locality_type_year",
        ),
    )
