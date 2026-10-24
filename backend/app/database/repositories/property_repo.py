"""Repository for physical property records and spatial radius queries.

Enforces GEMINI.md Section 4.2 and Section 8:
- Spatial distance searches using PostGIS or Haversine fallback.
- Invariant 8: State isolation - never matches properties across state boundaries.
"""

from __future__ import annotations

import math
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.property import PropertyRecord
from app.schemas.property import PropertyRecordCreate


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Standard Haversine formula returning distance in meters."""
    R = 6371000.0  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


class PropertyRepository:
    """Async repository for PropertyRecord CRUD and spatial proximity searches."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, record: PropertyRecordCreate) -> PropertyRecord:
        """Create a new PropertyRecord entity with PostGIS point geometry."""
        location_geom = None
        if record.latitude is not None and record.longitude is not None:
            location_geom = f"SRID=4326;POINT({record.longitude} {record.latitude})"

        entity = PropertyRecord(
            source_id=record.source_id,
            source_record_id=record.source_record_id,
            state_code=record.state_code.upper(),
            district=record.district,
            city=record.city,
            locality=record.locality,
            pincode=record.pincode,
            property_type=record.property_type.value if hasattr(record.property_type, "value") else str(record.property_type),
            area_value_raw=record.area_value_raw,
            area_unit_raw=record.area_unit_raw,
            area_sqft=record.area_sqft,
            area_type=record.area_type.value if hasattr(record.area_type, "value") else str(record.area_type),
            bedrooms=record.bedrooms,
            bathrooms=record.bathrooms,
            construction_year=record.construction_year,
            latitude=record.latitude,
            longitude=record.longitude,
            location=location_geom,
            source_authenticity_status=record.source_authenticity_status.value if hasattr(record.source_authenticity_status, "value") else str(record.source_authenticity_status),
            attribute_verification_status=record.attribute_verification_status.value if hasattr(record.attribute_verification_status, "value") else str(record.attribute_verification_status),
            source_url=record.source_url,
            source_record_hash=record.source_record_hash,
            raw_payload=record.raw_payload,
            published_at=record.published_at,
        )
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def get_by_id(self, property_id: UUID) -> PropertyRecord | None:
        stmt = select(PropertyRecord).where(PropertyRecord.property_id == property_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_nearby(
        self,
        lat: float,
        lon: float,
        radius_km: float,
        state_code: str,
        property_type: str | None = None,
    ) -> list[tuple[PropertyRecord, float]]:
        """Find properties within radius_km in the same state, returning (property, distance_meters).

        Enforces State Isolation: only searches properties within state_code.
        """
        radius_meters = radius_km * 1000.0
        state_norm = state_code.strip().upper()

        # Query candidates strictly isolated to the subject state
        stmt = select(PropertyRecord).where(
            PropertyRecord.state_code == state_norm,
            PropertyRecord.latitude.isnot(None),
            PropertyRecord.longitude.isnot(None),
        )
        if property_type:
            stmt = stmt.where(PropertyRecord.property_type == property_type)

        result = await self.session.execute(stmt)
        candidates = result.scalars().all()

        nearby: list[tuple[PropertyRecord, float]] = []
        for prop in candidates:
            if prop.latitude is None or prop.longitude is None:
                continue
            dist_m = haversine_distance_meters(lat, lon, prop.latitude, prop.longitude)
            if dist_m <= radius_meters:
                nearby.append((prop, round(dist_m, 1)))

        # Sort by proximity
        nearby.sort(key=lambda x: x[1])
        return nearby
