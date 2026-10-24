"""Canonical Pydantic v2 schemas for Transactions, Listings, and Reference Rates.

Enforces GEMINI.md Sections 4.3, 4.4, and 4.5:
- Invariant: Transactions, listings, and reference rates are separate schemas.
- Invariant: Circle rates/guidance values must NEVER be treated as sale transactions.
- Invariant: Asking prices must NEVER be treated as verified transaction prices.
"""

from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class PriceType(StrEnum):
    SALE_CONSIDERATION = "sale_consideration"
    REPORTED_SALE_PRICE = "reported_sale_price"
    UNKNOWN = "unknown"


class TransactionVerificationStatus(StrEnum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    REJECTED = "rejected"


class PropertyTransactionBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    source_id: UUID
    source_transaction_id: str = Field(..., min_length=1, max_length=100)
    property_id: UUID | None = None
    transaction_date: date
    transaction_price_raw: float = Field(..., gt=0)
    transaction_price_unit_raw: str = Field(..., min_length=1, max_length=20)
    transaction_price_inr: float | None = Field(default=None, gt=0)
    price_type: PriceType = PriceType.UNKNOWN
    transaction_verification_status: TransactionVerificationStatus = TransactionVerificationStatus.UNVERIFIED
    source_url: str = Field(..., min_length=5)
    source_record_hash: str = Field(..., min_length=16, max_length=64)
    raw_payload: dict[str, Any] | None = None


class PropertyTransactionCreate(PropertyTransactionBase):
    pass


class PropertyTransactionRead(PropertyTransactionBase):
    transaction_id: UUID = Field(default_factory=uuid4)
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ListingStatus(StrEnum):
    ACTIVE = "active"
    PENDING = "pending"
    SOLD = "sold"
    WITHDRAWN = "withdrawn"


class PropertyListingBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    source_id: UUID
    source_listing_id: str = Field(..., min_length=1, max_length=100)
    property_id: UUID | None = None
    asking_price_raw: float = Field(..., gt=0)
    asking_price_inr: float | None = Field(default=None, gt=0)
    listing_date: date
    listing_status: ListingStatus = ListingStatus.ACTIVE
    source_url: str = Field(..., min_length=5)
    source_record_hash: str = Field(..., min_length=16, max_length=64)


class PropertyListingCreate(PropertyListingBase):
    pass


class PropertyListingRead(PropertyListingBase):
    listing_id: UUID = Field(default_factory=uuid4)
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ReferenceRateBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    source_id: UUID
    state_code: str = Field(..., min_length=2, max_length=10)
    district: str = Field(..., min_length=1, max_length=100)
    locality: str = Field(..., min_length=1, max_length=150)
    property_category: str = Field(..., min_length=1, max_length=50)
    rate_raw: float = Field(..., gt=0)
    rate_unit_raw: str = Field(..., min_length=1, max_length=30)
    rate_inr_per_sqft: float | None = Field(
        default=None,
        gt=0,
        description="Normalized reference rate in INR per SQUARE FOOT (never per square metre).",
    )
    effective_from: date
    effective_to: date | None = None
    published_at: date | None = None
    source_url: str = Field(..., min_length=5)
    source_record_hash: str = Field(..., min_length=16, max_length=64)


class ReferenceRateCreate(ReferenceRateBase):
    pass


class ReferenceRateRead(ReferenceRateBase):
    rate_id: UUID = Field(default_factory=uuid4)
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
