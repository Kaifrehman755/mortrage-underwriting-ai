"""SQLAlchemy ORM model for Property Records with PostGIS spatial point.

Enforces GEMINI.md Section 4.2:
- Stable property identity and verified attributes.
- PostGIS Point geography/geometry for spatial distance searches.
- Unique constraint on (source_id, source_record_id).
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from geoalchemy2 import Geometry
from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class PropertyRecord(Base, TimestampMixin):
    """Stores physical residential property identity, attributes, and geographic coordinates."""

    __tablename__ = "property_records"

    property_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    source_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("data_sources.source_id"), nullable=False, index=True
    )
    source_record_id: Mapped[str] = mapped_column(String(100), nullable=False)
    state_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    locality: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    property_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    area_value_raw: Mapped[float] = mapped_column(Float, nullable=False)
    area_unit_raw: Mapped[str] = mapped_column(String(30), nullable=False)
    area_sqft: Mapped[float | None] = mapped_column(Float, nullable=True)
    area_type: Mapped[str] = mapped_column(String(30), nullable=False, default="unknown", index=True)

    bedrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bathrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    construction_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # PostGIS spatial point (EPSG 4326 - WGS 84)
    location = mapped_column(
        Geometry(geometry_type="POINT", srid=4326), nullable=True
    )

    source_authenticity_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="unverified"
    )
    attribute_verification_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="unverified"
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_record_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "source_id", "source_record_id", name="uq_property_record_source_source_id"
        ),
        Index("idx_property_record_location", location, postgresql_using="gist"),
    )
