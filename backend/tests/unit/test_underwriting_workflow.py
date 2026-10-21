
"""Tests for the mortgage underwriting LangGraph workflow."""

import pytest

from app.workflows.underwriting_graph import build_underwriting_graph


@pytest.mark.asyncio
async def test_incomplete_application_routes_to_human_review():
    """An application without assessment results must not be approved."""

    graph = build_underwriting_graph()

    result = await graph.ainvoke({
        "application_id": "TEST-001",
    })

    assert result["application_id"] == "TEST-001"
    assert result["human_review_required"] is True
    assert result["decision_recommendation"]["recommendation"] == "SUSPEND"
    assert result["decision_recommendation"]["requires_human_review"] is True



@pytest.mark.asyncio
async def test_valid_existing_recommendation_can_be_finalized():
    """A complete application with valid test assessment data can finalize."""

    graph = build_underwriting_graph()

    result = await graph.ainvoke({
        "application_id": "TEST-002",
        "human_review_required": False,

        # Financial inputs belong inside extracted_data.
        "extracted_data": {
            "gross_monthly_income": 6000,
            "total_monthly_debt": 1800,
            "loan_amount": 240000,
            "property_value": 300000,
            "primary_loan": 240000,
            "additional_secured_loans": 15000,
            "net_operating_income": 125000,
            "annual_debt_service": 100000,
            "fico_score": 740,
            "reserves_months": 6,
        },

        # Decision assessment fields belong at the top level.
        "documents_complete": True,
        "compliance_assessment": {
            "status": "completed",
            "clear": True,
            "flags": [],
        },
        "data_conflicts": False,
        "confidence": 0.95,
        "policy_outcome": "pass",
    })

    assert result["application_id"] == "TEST-002"
    assert result["financial_calculation_status"] == "completed"
    assert result["human_review_required"] is False
    assert result["decision_recommendation"]["recommendation"] == "APPROVE"
    assert result["decision_recommendation"]["requires_human_review"] is False




@pytest.mark.asyncio
async def test_invalid_finalization_is_suspended():
    """A missing recommendation must not pass finalization."""

    graph = build_underwriting_graph()

    result = await graph.ainvoke({
        "application_id": "TEST-003",
        "human_review_required": False,
    })

    assert result["human_review_required"] is True
    assert result["decision_recommendation"]["recommendation"] == "SUSPEND"
    assert result["decision_recommendation"]["requires_human_review"] is True


@pytest.mark.parametrize(
    "assessment",
    [
        # Assessment has not completed.
        {"status": "pending", "clear": True, "flags": []},

        # The clearance value must be a Boolean.
        {"status": "completed", "clear": "true", "flags": []},

        # Flags must be supplied as a list.
        {"status": "completed", "clear": True, "flags": "none"},

        # Unresolved flags must prevent clearance.
        {
            "status": "completed",
            "clear": True,
            "flags": ["Unresolved compliance concern"],
        },
    ],
)
@pytest.mark.asyncio
async def test_invalid_compliance_assessment_requires_review(assessment):
    """Invalid or unresolved compliance assessments must not be approved."""

    graph = build_underwriting_graph()

    result = await graph.ainvoke({
        "application_id": "TEST-COMPLIANCE",
        "human_review_required": False,
        "extracted_data": {
            "gross_monthly_income": 6000,
            "total_monthly_debt": 1800,
            "loan_amount": 240000,
            "property_value": 300000,
            "primary_loan": 240000,
            "additional_secured_loans": 15000,
            "net_operating_income": 125000,
            "annual_debt_service": 100000,
            "fico_score": 740,
            "reserves_months": 6,
        },
        "documents_complete": True,
        "compliance_assessment": assessment,
        "data_conflicts": False,
        "confidence": 0.95,
        "policy_outcome": "pass",
    })

    assert result["compliance_clear"] is False
    assert result["human_review_required"] is True
    assert result["decision_recommendation"]["recommendation"] == "SUSPEND"
    assert result["decision_recommendation"]["requires_human_review"] is True


@pytest.mark.asyncio
async def test_existing_human_review_requirement_is_not_overridden():
    """A prior review requirement must not silently become an approval."""

    graph = build_underwriting_graph()

    result = await graph.ainvoke({
        "application_id": "TEST-EXISTING-REVIEW",
        "human_review_required": True,
        "extracted_data": {
            "gross_monthly_income": 6000,
            "total_monthly_debt": 1800,
            "loan_amount": 240000,
            "property_value": 300000,
            "primary_loan": 240000,
            "additional_secured_loans": 15000,
            "net_operating_income": 125000,
            "annual_debt_service": 100000,
            "fico_score": 740,
            "reserves_months": 6,
        },
        "documents_complete": True,
        "compliance_assessment": {
            "status": "completed",
            "clear": True,
            "flags": [],
        },
        "data_conflicts": False,
        "confidence": 0.95,
        "policy_outcome": "pass",
    })

    assert result["human_review_required"] is True
    assert result["decision_recommendation"]["recommendation"] == "SUSPEND"
    assert result["decision_recommendation"]["requires_human_review"] is True
