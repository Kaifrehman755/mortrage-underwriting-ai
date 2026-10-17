"""Quarantine dataset models, reason codes, and row-accounting invariants.

Enforces GEMINI.md Section 4.6 and Section 6:
- Every invalid row is recorded with a reason code and audit detail.
- Row-accounting invariant: rows_received == rows_accepted + rows_quarantined + rows_duplicate + rows_rejected.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class QuarantineReason(str, Enum):
    MISSING_PRICE = "MISSING_PRICE"
    MISSING_AREA = "MISSING_AREA"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_UNIT = "INVALID_UNIT"
    INVALID_DATE = "INVALID_DATE"
    INVALID_COORDINATES = "INVALID_COORDINATES"
    UNSUPPORTED_PROPERTY_TYPE = "UNSUPPORTED_PROPERTY_TYPE"
    DUPLICATE_RECORD = "DUPLICATE_RECORD"
    SOURCE_NOT_APPROVED = "SOURCE_NOT_APPROVED"
    PRICE_TYPE_NOT_ELIGIBLE = "PRICE_TYPE_NOT_ELIGIBLE"
    AREA_BASIS_INCOMPATIBLE = "AREA_BASIS_INCOMPATIBLE"
    PROVENANCE_MISSING = "PROVENANCE_MISSING"


class QuarantineRecord(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    quarantine_id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    source_id: UUID
    source_record_id: str | None = None
    reason_code: QuarantineReason
    reason_detail: str = Field(..., min_length=2)
    rejected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    raw_record_ref: str = Field(..., min_length=1, description="Pointer, hash, or permitted snapshot of raw row")


class IngestionRunAccounting(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    run_id: UUID = Field(default_factory=uuid4)
    source_id: UUID
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    build_version: str = Field(..., min_length=1)
    source_snapshot_hash: str = Field(..., min_length=16, max_length=64)
    rows_received: int = Field(default=0, ge=0)
    rows_accepted: int = Field(default=0, ge=0)
    rows_quarantined: int = Field(default=0, ge=0)
    rows_duplicate: int = Field(default=0, ge=0)
    # F-15: reserved field. The current validators route every invalid row to quarantine with a
    # reason code, so rows_rejected is 0 today; it is kept for a future "structurally unusable
    # row" category and remains part of the accounting invariant.
    rows_rejected: int = Field(default=0, ge=0)
    error_summary: str | None = None

    @model_validator(mode="after")
    def verify_accounting_invariant(self) -> "IngestionRunAccounting":
        """In GEMINI.md Section 4.6: Every ingestion run must account for all received rows."""
        total_accounted = self.rows_accepted + self.rows_quarantined + self.rows_duplicate + self.rows_rejected
        if self.finished_at is not None and self.rows_received != total_accounted:
            raise ValueError(
                f"Row accounting invariant violated: rows_received ({self.rows_received}) != "
                f"accepted({self.rows_accepted}) + quarantined({self.rows_quarantined}) + "
                f"duplicate({self.rows_duplicate}) + rejected({self.rows_rejected}) = {total_accounted}"
            )
        return self
