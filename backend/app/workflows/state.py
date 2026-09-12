"""LangGraph state definitions for mortgage underwriting workflows (Reserved for Phase 1+)."""

from typing import Any

from typing_extensions import TypedDict


class UnderwritingState(TypedDict, total=False):
    """Workflow state schema passed across LangGraph nodes."""

    application_id: str
    documents: list[dict[str, Any]]
    extracted_data: dict[str, Any]
    calculations: dict[str, float]
    compliance_flags: list[dict[str, Any]]
    credit_analysis: dict[str, Any]
    property_valuation: dict[str, Any]
    decision_recommendation: dict[str, Any] | None
    human_review_required: bool
    audit_trail: list[dict[str, Any]]
