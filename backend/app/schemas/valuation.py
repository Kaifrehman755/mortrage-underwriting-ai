"""Canonical Pydantic v2 schemas for Valuation Runs and Comparables.

Enforces GEMINI.md Section 4.7:
- Valuation traceability, comparable evidence auditing, and abstention states.
"""

from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ValuationStatus(StrEnum):
    COMPLETED = "completed"
    ABSTAINED = "abstained"
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    FAILED = "failed"


class ValuationComparableRead(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    valuation_id: UUID
    transaction_id: UUID
    distance_m: float = Field(..., ge=0.0)
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    adjusted_price_per_sqft: float = Field(..., gt=0.0)
    selection_reason: str = Field(..., min_length=2)


class ValuationRunBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    subject_property_input: dict[str, Any]
    estimate_inr: float | None = Field(default=None, gt=0)
    lower_bound_inr: float | None = Field(default=None, gt=0)
    upper_bound_inr: float | None = Field(default=None, gt=0)
    status: ValuationStatus = ValuationStatus.NEEDS_HUMAN_REVIEW
    reason_codes: list[str] = Field(default_factory=list)
    method_version: str = Field(..., min_length=1)
    dataset_cutoff: date

    @model_validator(mode="after")
    def validate_bounds_and_status(self) -> "ValuationRunBase":
        if self.status == ValuationStatus.COMPLETED:
            if self.estimate_inr is None:
                raise ValueError("Completed valuation must have an estimate_inr")
            if self.lower_bound_inr is not None and self.upper_bound_inr is not None:
                if self.lower_bound_inr > self.upper_bound_inr:
                    raise ValueError(
                        f"lower_bound_inr ({self.lower_bound_inr}) cannot exceed upper_bound_inr ({self.upper_bound_inr})"
                    )
                if not (self.lower_bound_inr <= self.estimate_inr <= self.upper_bound_inr):
                    raise ValueError(
                        f"estimate_inr ({self.estimate_inr}) must be within bounds [{self.lower_bound_inr}, {self.upper_bound_inr}]"
                    )
        elif self.status in (ValuationStatus.ABSTAINED, ValuationStatus.NEEDS_HUMAN_REVIEW):
            if not self.reason_codes:
                raise ValueError(
                    f"Valuations with status '{self.status}' must provide at least one reason code explaining the abstention/review."
                )
        return self


class ValuationRunCreate(ValuationRunBase):
    pass


class ValuationRunRead(ValuationRunBase):
    valuation_id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    comparables: list[ValuationComparableRead] = Field(default_factory=list)
