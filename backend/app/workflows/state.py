
"""LangGraph state definitions for mortgage underwriting workflows."""

from typing import Any
from typing_extensions import TypedDict


class UnderwritingState(TypedDict, total=False):
    """Shared state passed between underwriting workflow nodes."""

    application_id: str

    # Document ingestion
    documents: list[dict[str, Any]]
    extracted_data: dict[str, Any]

    # Financial calculations
    calculations: dict[str, Any]
    financial_calculation_status: str
    financial_calculation_warnings: list[str]

    # Credit and property assessment
    credit_analysis: dict[str, Any]
    property_valuation: dict[str, Any]

    # Compliance
    compliance_flags: list[dict[str, Any]]
    compliance_assessment: dict[str, Any]
    compliance_status: str
    compliance_clear: bool

    # Decision and human review
    decision_recommendation: dict[str, Any] | None
    human_review_required: bool
    documents_complete: bool
    compliance_clear: bool
    data_conflicts: bool
    confidence: float
    policy_outcome: str

    # Audit
    audit_trail: list[dict[str, Any]]
