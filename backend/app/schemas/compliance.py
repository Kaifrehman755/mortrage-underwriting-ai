"""Pydantic schemas for the stateless compliance-check API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.compliance.schemas import ComplianceOutput
from app.property.schemas import ComparableRecord, SubjectProperty, ValuationOutput
from app.rag.schemas import EvidenceItem

_RAW_IDENTIFIER_KEYS = {
    "aadhaar",
    "aadhaar_number",
    "account_number",
    "bank_account_number",
    "pan",
    "pan_number",
}


class ComplianceCheckRequest(BaseModel):
    """Case data required to run the deterministic compliance rule pack."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    case_id: str = Field(..., min_length=1)
    subject: SubjectProperty
    loan_data: dict[str, Any] = Field(default_factory=dict)
    valuation: ValuationOutput | None = None
    market_facts: list[ComparableRecord] = Field(default_factory=list)
    market_indicators: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def reject_raw_identifiers(self) -> ComplianceCheckRequest:
        """Reject raw KYC identifiers; only verification statuses are accepted."""
        raw_keys = _find_raw_identifier_keys(self.loan_data)
        if raw_keys:
            raise ValueError(
                "Raw KYC identifiers are not accepted by this API; send verification "
                f"statuses only (found: {', '.join(sorted(raw_keys))})"
            )
        return self


class ComplianceCheckResponse(BaseModel):
    """Compliance findings, evidence references and the human-review gate."""

    case_id: str
    status: str
    rule_set_version: str
    findings: list[ComplianceOutput] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    human_review_required: bool


def _find_raw_identifier_keys(value: Any, prefix: str = "") -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key).strip().lower()
            path = f"{prefix}.{key_text}" if prefix else key_text
            if key_text in _RAW_IDENTIFIER_KEYS:
                found.add(path)
            found.update(_find_raw_identifier_keys(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.update(_find_raw_identifier_keys(child, f"{prefix}[{index}]"))
    return found
