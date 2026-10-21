
"""Unit tests for the LangGraph financial calculation node."""

import pytest

from app.workflows.nodes import financial_calculation_node


def valid_application_data():
    """Return a complete sample application for testing."""

    return {
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
    }


@pytest.mark.asyncio
async def test_complete_application_calculates_all_metrics():
    """All six calculation results should be returned."""

    result = await financial_calculation_node({
        "application_id": "FIN-001",
        "extracted_data": valid_application_data(),
    })

    assert result["financial_calculation_status"] == "completed"
    assert result["human_review_required"] is False

    calculations = result["calculations"]

    assert calculations["dti"]["dti_percentage"] == 30
    assert calculations["ltv"]["ltv"] == 80
    assert calculations["cltv"]["cltv"] == 85
    assert calculations["dscr"]["dscr"] == 1.25
    assert calculations["credit_analysis"]["credit_category"] == "Very Good"
    assert calculations["risk_score"] == 26.0


@pytest.mark.asyncio
async def test_missing_extracted_data_requires_human_review():
    """Missing extracted data must not produce financial results."""

    result = await financial_calculation_node({
        "application_id": "FIN-002",
    })

    assert result["human_review_required"] is True
    assert result["financial_calculation_status"] == "invalid"
    assert "calculations" not in result


@pytest.mark.asyncio
async def test_missing_required_field_requires_human_review():
    """Incomplete financial inputs must be flagged."""

    data = valid_application_data()
    del data["gross_monthly_income"]

    result = await financial_calculation_node({
        "application_id": "FIN-003",
        "extracted_data": data,
    })

    assert result["human_review_required"] is True
    assert result["financial_calculation_status"] == "incomplete"
    assert any(
        "gross_monthly_income" in warning
        for warning in result["financial_calculation_warnings"]
    )


@pytest.mark.asyncio
async def test_invalid_property_value_requires_human_review():
    """A zero property value must not produce a completed assessment."""

    data = valid_application_data()
    data["property_value"] = 0

    result = await financial_calculation_node({
        "application_id": "FIN-004",
        "extracted_data": data,
    })

    assert result["human_review_required"] is True
    assert result["financial_calculation_status"] == "invalid"
    assert "calculations" not in result


@pytest.mark.asyncio
async def test_invalid_fico_score_requires_human_review():
    """An out-of-range FICO score must not pass calculation."""

    data = valid_application_data()
    data["fico_score"] = 900

    result = await financial_calculation_node({
        "application_id": "FIN-005",
        "extracted_data": data,
    })

    assert result["human_review_required"] is True
    assert result["financial_calculation_status"] == "invalid"
    assert "calculations" not in result

@pytest.mark.asyncio
async def test_successful_calculation_preserves_existing_review_flag():
    """Successful calculations must not clear an earlier review requirement."""
    state = {
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
    }

    result = await financial_calculation_node(state)

    assert result["financial_calculation_status"] == "completed"
    assert result["human_review_required"] is True


@pytest.mark.asyncio
async def test_fico_list_selects_qualifying_score_for_credit_and_risk(
    monkeypatch,
):
    """The qualifying FICO score must be used by credit and risk analysis."""
    data = valid_application_data()
    data.pop("fico_score")
    data["fico_scores"] = [720, 680, 750]

    captured_risk_inputs = {}

    def fake_risk_score(**kwargs):
        captured_risk_inputs.update(kwargs)
        return 26.0

    monkeypatch.setattr(
        "app.workflows.nodes.compute_composite_risk_score",
        fake_risk_score,
    )

    result = await financial_calculation_node({
        "application_id": "FIN-FICO-LIST-001",
        "extracted_data": data,
    })

    assert result["financial_calculation_status"] == "completed"
    assert result["human_review_required"] is False

    calculations = result["calculations"]

    # The middle score of [720, 680, 750] is 720.
    assert calculations["credit_analysis"]["fico_score"] == 720
    assert calculations["credit_analysis"]["credit_category"] == "Good"
    assert captured_risk_inputs["fico"] == 720


@pytest.mark.asyncio
async def test_fico_list_takes_precedence_when_both_inputs_are_supplied(
    monkeypatch,
):
    """When both inputs exist, the FICO list determines the selected score."""
    data = valid_application_data()
    data["fico_score"] = 740
    data["fico_scores"] = [720, 680, 750]

    captured_risk_inputs = {}

    def fake_risk_score(**kwargs):
        captured_risk_inputs.update(kwargs)
        return 26.0

    monkeypatch.setattr(
        "app.workflows.nodes.compute_composite_risk_score",
        fake_risk_score,
    )

    result = await financial_calculation_node({
        "application_id": "FIN-FICO-LIST-002",
        "extracted_data": data,
    })

    assert result["financial_calculation_status"] == "completed"
    assert result["calculations"]["credit_analysis"]["fico_score"] == 720
    assert captured_risk_inputs["fico"] == 720


@pytest.mark.asyncio
async def test_invalid_fico_list_requires_human_review():
    """An invalid score in the FICO list must block financial calculations."""
    data = valid_application_data()
    data.pop("fico_score")
    data["fico_scores"] = [720, 900]

    result = await financial_calculation_node({
        "application_id": "FIN-FICO-LIST-003",
        "extracted_data": data,
    })

    assert result["financial_calculation_status"] == "invalid"
    assert result["human_review_required"] is True
    assert "calculations" not in result
    assert result["financial_calculation_warnings"]



@pytest.mark.asyncio
async def test_missing_all_fico_inputs_requires_human_review():
    """An application without either supported FICO input is incomplete."""
    data = valid_application_data()
    data.pop("fico_score")
    data.pop("fico_scores", None)

    result = await financial_calculation_node({
        "application_id": "FIN-MISSING-FICO",
        "extracted_data": data,
    })

    assert result["financial_calculation_status"] == "incomplete"
    assert result["human_review_required"] is True
    assert any(
        "Missing FICO data" in warning
        for warning in result["financial_calculation_warnings"]
    )
    assert "calculations" not in result

