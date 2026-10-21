
import pytest

from app.calculations.validation import to_finite_decimal

from app.workflows.nodes import (
    _to_decimal,
    decision_synthesis_node,
    finalize_decision_node,
    financial_calculation_node,
)


@pytest.mark.parametrize(
    "value",
    [True, None, "not-a-number", "NaN", "Infinity"],
)
def test_to_decimal_rejects_invalid_values(value):
    """Invalid and non-finite values must not enter financial calculations."""

    with pytest.raises(ValueError):
        _to_decimal(value, "test_field")


def valid_extracted_data():
    """Return valid financial inputs for workflow-node tests."""

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
async def test_financial_node_rejects_invalid_reserves():
    """Reserves must be numeric before risk scoring."""

    data = valid_extracted_data()
    data["reserves_months"] = "six"

    result = await financial_calculation_node({
        "application_id": "TEST-RESERVES",
        "extracted_data": data,
    })

    assert result["financial_calculation_status"] == "invalid"
    assert result["human_review_required"] is True


@pytest.mark.asyncio
async def test_financial_node_rejects_invalid_credit_agent_result(monkeypatch):
    """An invalid CreditAgent response must not be trusted."""

    def invalid_credit_result(self, fico_score):
        return {"status": "failed"}

    monkeypatch.setattr(
        "app.workflows.nodes.CreditAgent.analyze",
        invalid_credit_result,
    )

    result = await financial_calculation_node({
        "application_id": "TEST-CREDIT-AGENT",
        "extracted_data": valid_extracted_data(),
    })

    assert result["financial_calculation_status"] == "invalid"
    assert result["human_review_required"] is True
    assert any(
        "CreditAgent returned an invalid result" in warning
        for warning in result["financial_calculation_warnings"]
    )


@pytest.mark.asyncio
async def test_decision_node_suspends_when_calculations_are_not_a_dictionary():
    """Missing calculation results must suspend decision synthesis."""

    result = await decision_synthesis_node({
        "financial_calculation_status": "completed",
        "calculations": None,
    })

    assert result["human_review_required"] is True
    assert result["decision_recommendation"]["recommendation"] == "SUSPEND"


@pytest.mark.asyncio
async def test_decision_node_suspends_when_calculation_fields_are_missing():
    """Malformed calculation output must not produce an automatic decision."""

    result = await decision_synthesis_node({
        "financial_calculation_status": "completed",
        "calculations": {"dti": {}},
    })

    assert result["human_review_required"] is True
    assert result["decision_recommendation"]["recommendation"] == "SUSPEND"
    assert result["decision_recommendation"]["requires_human_review"] is True


@pytest.mark.asyncio
async def test_finalize_node_suspends_invalid_recommendation():
    """A suspended recommendation cannot pass finalization."""

    result = await finalize_decision_node({
        "human_review_required": False,
        "decision_recommendation": {
            "recommendation": "SUSPEND",
            "requires_human_review": True,
            "reasons": ["Review required."],
        },
    })

    assert result["human_review_required"] is True
    assert result["decision_recommendation"]["recommendation"] == "SUSPEND"
    assert result["decision_recommendation"]["requires_human_review"] is True


@pytest.mark.asyncio
async def test_financial_node_rejects_boolean_fico_score():
    """A Boolean must not be accepted as a FICO score."""

    data = valid_extracted_data()
    data["fico_score"] = True

    result = await financial_calculation_node({
        "application_id": "TEST-INVALID-FICO-TYPE",
        "extracted_data": data,
    })

    assert result["financial_calculation_status"] == "invalid"
    assert result["human_review_required"] is True
    assert any(
        "fico_score must be an integer" in warning
        for warning in result["financial_calculation_warnings"]
    )


@pytest.mark.asyncio
async def test_financial_node_handles_invalid_dti_result():
    """A zero gross income must not proceed through underwriting."""

    data = valid_extracted_data()
    data["gross_monthly_income"] = 0

    result = await financial_calculation_node({
        "application_id": "TEST-INVALID-DTI",
        "extracted_data": data,
    })

    assert result["financial_calculation_status"] == "invalid"
    assert result["human_review_required"] is True
    assert result["financial_calculation_warnings"]

def test_shared_validation_rejects_unsupported_type():
    """Unsupported Python objects must not enter financial calculations."""
    with pytest.raises(ValueError, match="test_field must be a valid number"):
        to_finite_decimal(object(), "test_field")


def test_shared_validation_rejects_malformed_numeric_string():
    """Malformed numeric strings must produce a clear validation error."""
    with pytest.raises(ValueError, match="test_field must be a valid number"):
        to_finite_decimal("not-a-number", "test_field")
