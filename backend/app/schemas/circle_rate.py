"""Pydantic schemas for circle rate API endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CircleRateLookup(BaseModel):
    """Circle rate lookup result with source metadata for user verification."""

    model_config = ConfigDict(from_attributes=True)

    state: str
    district: str
    zone_tehsil: str
    locality: str
    property_type: str
    rate_per_sqm: float = Field(
        gt=0,
        description=(
            "Government-notified circle rate in INR per SQUARE METRE "
            "(not per square foot)."
        ),
    )
    effective_year: int = Field(ge=1900, le=2100)
    source_url: str
    fetched_at: datetime
