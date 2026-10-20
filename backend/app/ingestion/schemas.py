"""Normalized circle rate record contract for ingestion."""

from datetime import datetime

from pydantic import BaseModel, Field


class CircleRateRecord(BaseModel):
    """A single circle rate row cleaned into the canonical schema."""

    model_config = {"frozen": True}

    state: str
    district: str
    zone_tehsil: str
    locality: str
    property_type: str
    rate_per_sqm: float = Field(gt=0)
    effective_year: int = Field(ge=1900, le=2100)
    source_url: str
    fetched_at: datetime
