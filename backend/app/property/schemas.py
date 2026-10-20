"""Pydantic v2 schemas and data contracts for the Property Underwriting Agent.

Strictly enforces Playbook Section 1 invariants:
1. Never fabricate MLS or property data; no data means abstain and escalate.
2. Market facts (comparable_sale) and model estimates (valuation_run) live in separate objects.
4. Any failure or low confidence sets human_review_required.
5. No protected-class proxies as valuation features.
6. The LLM explainer cannot change flags, severity or the estimate.
"""

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


class SubjectProperty(BaseModel):
    """Normalized subject property under appraisal consideration."""

    property_id: str = Field(default_factory=lambda: str(uuid4()))
    original_address: str
    address_norm: str
    locality: str
    city: str
    state_code: str = Field(..., min_length=2, max_length=2)
    pincode: str | None = None
    property_type: str = "apartment"
    beds: float | None = None
    baths: float | None = None
    living_area_sqft: float = Field(..., gt=0)
    area_basis: Literal["carpet", "built_up", "super_built_up"] = "carpet"
    year_built: int | None = None
    floor_no: int | None = None
    total_floors: int | None = None
    lat: float
    lon: float
    geocode_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    quoted_price: float | None = None


class ComparableRecord(BaseModel):
    """Market facts retrieved from authorized providers. Never modelled or fabricated."""

    comp_id: str = Field(default_factory=lambda: str(uuid4()))
    source_id: int = 1
    source_name: str
    provider_record_id: str
    property_id: str = Field(default_factory=lambda: str(uuid4()))
    address: str
    locality: str
    city: str
    state_code: str = Field(..., min_length=2, max_length=2)
    property_type: str
    sale_price: float = Field(..., gt=0)
    currency: str = "INR"
    sale_date: str
    living_area_sqft: float = Field(..., gt=0)
    price_per_sqft: float
    price_type: Literal["registered_deed", "valuer_report", "asking", "survey"]
    area_basis: Literal["carpet", "built_up", "super_built_up"] = "carpet"
    license_scope: str
    clean_flags: list[str] = Field(default_factory=list)
    distance_km: float | None = None
    fetched_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    is_synthetic: bool = False
    raw: dict[str, Any] | None = None

    @field_validator("price_per_sqft", mode="before")
    @classmethod
    def calculate_price_per_sqft(cls, v: Any, info: Any) -> float:
        if v is not None:
            return float(v)
        data = info.data
        if "sale_price" in data and "living_area_sqft" in data and data["living_area_sqft"] > 0:
            return round(data["sale_price"] / data["living_area_sqft"], 2)
        return 0.0


class MarketIndicator(BaseModel):
    """Locality or city level aggregate market metrics."""

    geo_key: str
    period: str
    metric: str
    value: float
    source_name: str
    source_id: int = 1


class ValuationOutput(BaseModel):
    """Model output strictly separated from market facts.

    Invariant 2: Market facts and model estimates live in separate fields and objects.
    Invariant 4: Low confidence or failure sets human_review_required.
    """

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    case_id: str
    subject_id: str
    estimate: float | None = None
    interval_low: float | None = None
    interval_high: float | None = None
    confidence_level: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence_label: Literal["low", "medium", "high"] = "low"
    method: str = "weighted_median_ppsf"
    n_comps: int = 0
    comp_ids: list[str] = Field(default_factory=list)
    dispersion: float | None = None
    abstain_reason: str | None = None
    model_version: str = "1.0.0"
    is_estimate: bool = True
    evidence_is_synthetic: bool = False
    market_indicators: dict[str, Any] = Field(default_factory=dict)
    human_review_required: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    @model_validator(mode="after")
    def validate_estimate_or_abstain(self) -> "ValuationOutput":
        # Invariant: is_estimate must ALWAYS be true
        if not self.is_estimate:
            raise ValueError("Valuation output must declare is_estimate=True")

        # Must have either a valid estimate or an explicit abstain reason
        if self.estimate is None and not self.abstain_reason:
            raise ValueError("Valuation output requires either an estimate or an abstain_reason.")

        # If abstained, estimate must be None
        if self.abstain_reason and self.estimate is not None:
            raise ValueError("Abstained valuation output cannot contain an estimate.")

        # If confidence is low or abstained, human_review_required MUST be True
        if self.abstain_reason is not None or self.confidence_label == "low":
            self.human_review_required = True

        return self


class AuditEvent(BaseModel):
    """Audit log entry with sha256 digests for end-to-end immutability and tracing."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    case_id: str
    actor: str = "property_agent"
    node: str = "property_valuation"
    input_digest: str
    output_digest: str
    model_version: str = "1.0.0"
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    details: dict[str, Any] = Field(default_factory=dict)


class SharedCaseState(BaseModel):
    """Shared case state across agent boundaries (Property, Compliance, Underwriting).

    Separates market_facts, model_output, evidence, and compliance.
    """

    case_id: str = Field(default_factory=lambda: str(uuid4()))
    subject_property: SubjectProperty
    loan_data: dict[str, Any] = Field(default_factory=dict)
    market_facts: list[ComparableRecord] = Field(default_factory=list)
    model_output: ValuationOutput | None = None
    market_indicators: dict[str, Any] = Field(default_factory=dict)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    compliance: list[dict[str, Any]] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    human_review_required: bool = False
    status: Literal["new", "intake_done", "valued", "abstained", "compliance_checked", "needs_review", "reviewed", "approved", "rejected"] = "new"
    audit_trail: list[AuditEvent] = Field(default_factory=list)
