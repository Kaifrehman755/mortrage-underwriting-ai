"""Canonical Pydantic v2 schemas for Data Sources and Provenance.

Enforces GEMINI.md Section 4.1:
- Provider identity, licensing, and approval gating.
"""

from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SourceType(str, Enum):
    GOVERNMENT = "government"
    AUTHORIZED_PROVIDER = "authorized_provider"
    MANUAL_AUTHORIZED_IMPORT = "manual_authorized_import"
    SYNTHETIC_TEST = "synthetic_test"


class ApprovalStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SUSPENDED = "suspended"
    REJECTED = "rejected"


class DataSourceBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    source_name: str = Field(..., min_length=2, max_length=100)
    state_code: str = Field(..., min_length=2, max_length=10, description="UP, MH, KA, TS, or ALL")
    source_type: SourceType
    official_url: str
    access_method: str = Field(..., min_length=2, max_length=50)
    license_scope: str = Field(..., min_length=3)
    approval_status: ApprovalStatus = ApprovalStatus.PENDING_REVIEW
    terms_url: str | None = None


class DataSourceCreate(DataSourceBase):
    pass


class DataSourceRead(DataSourceBase):
    source_id: UUID = Field(default_factory=uuid4)
    last_checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_successful_sync_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
