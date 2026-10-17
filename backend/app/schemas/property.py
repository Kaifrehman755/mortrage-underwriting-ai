"""Canonical Pydantic v2 schemas for Property Records.

Enforces GEMINI.md Section 4.2:
- Stable property identity, verified attributes, and area-type integrity.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PropertyType(str, Enum):
    APARTMENT = "apartment"
    INDEPENDENT_HOUSE = "independent_house"
    VILLA = "villa"
    RESIDENTIAL_PLOT = "residential_plot"
    OTHER_RESIDENTIAL = "other_residential"


class AreaType(str, Enum):
    CARPET = "carpet"
    BUILT_UP = "built_up"
    SUPER_BUILT_UP = "super_built_up"
    PLOT = "plot"
    UNKNOWN = "unknown"


class SourceAuthenticityStatus(str, Enum):
    VERIFIED_OFFICIAL = "verified_official"
    SECONDARY_PROVIDER = "secondary_provider"
    UNVERIFIED = "unverified"


class AttributeVerificationStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    DISPUTED = "disputed"


class PropertyRecordBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    source_id: UUID
    source_record_id: str = Field(..., min_length=1, max_length=100)
    state_code: str = Field(..., min_length=2, max_length=10)
    district: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    locality: str = Field(..., min_length=1, max_length=150)
    pincode: str | None = None
    property_type: PropertyType = PropertyType.APARTMENT
    area_value_raw: float = Field(..., gt=0)
    area_unit_raw: str = Field(..., min_length=1, max_length=30)
    area_sqft: float | None = Field(default=None, gt=0)
    area_type: AreaType = AreaType.UNKNOWN
    bedrooms: int | None = Field(default=None, ge=0)
    bathrooms: int | None = Field(default=None, ge=0)
    construction_year: int | None = Field(default=None, ge=1800, le=2100)
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    source_authenticity_status: SourceAuthenticityStatus = SourceAuthenticityStatus.UNVERIFIED
    attribute_verification_status: AttributeVerificationStatus = AttributeVerificationStatus.UNVERIFIED
    source_url: str = Field(..., min_length=5)
    source_record_hash: str = Field(..., min_length=16, max_length=64)
    raw_payload: dict[str, Any] | None = None
    published_at: datetime | None = None

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: str | None) -> str | None:
        if v is None:
            return None
        cleaned = v.strip()
        if not (cleaned.isdigit() and len(cleaned) == 6):
            raise ValueError(f"Indian PIN code must be exactly 6 digits, got '{v}'")
        return cleaned


class PropertyRecordCreate(PropertyRecordBase):
    pass


class PropertyRecordRead(PropertyRecordBase):
    property_id: UUID = Field(default_factory=uuid4)
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
