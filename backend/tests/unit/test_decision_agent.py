
import pytest

from app.agents.decision_agent import DecisionAgent


@pytest.fixture
def valid_assessment():
    return {
        "dti_percentage": 30.0,
        "ltv": 80.0,
        "cltv": 85.0,
        "dscr": 1.25,
        "fico_score": 740,
        "risk_score": 26.0,
        "documents_complete": True,
        "compliance_clear": True,
        "data_conflicts": False,
        "confidence": 0.95,
        "policy_outcome": "pass",
    }


def test_decision_agent_approves_policy_pass(valid_assessment):
    result = DecisionAgent().evaluate(valid_assessment)

    assert result["recommendation"] == "APPROVE"
    assert result["requires_human_review"] is False


def test_decision_agent_suspends_when_documents_missing(valid_assessment):
    valid_assessment["documents_complete"] = False

    result = DecisionAgent().evaluate(valid_assessment)

    assert result["recommendation"] == "SUSPEND"
    assert result["requires_human_review"] is True
    assert any("documents" in reason for reason in result["reasons"])


def test_decision_agent_suspends_when_confidence_is_low(valid_assessment):
    valid_assessment["confidence"] = 0.60

    result = DecisionAgent().evaluate(valid_assessment)

    assert result["recommendation"] == "SUSPEND"
    assert result["requires_human_review"] is True


def test_decision_agent_denies_policy_fail(valid_assessment):
    valid_assessment["policy_outcome"] = "fail"

    result = DecisionAgent().evaluate(valid_assessment)

    assert result["recommendation"] == "DENY"
    assert result["requires_human_review"] is False


def test_decision_agent_suspends_when_data_is_missing(valid_assessment):
    del valid_assessment["fico_score"]

    result = DecisionAgent().evaluate(valid_assessment)

    assert result["recommendation"] == "SUSPEND"
    assert result["requires_human_review"] is True
    assert any("fico_score" in reason for reason in result["reasons"])


def test_decision_agent_rejects_invalid_policy_outcome(valid_assessment):
    valid_assessment["policy_outcome"] = "unknown"

    with pytest.raises(ValueError):
        DecisionAgent().evaluate(valid_assessment)


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("dti_percentage", float("nan")),
        ("ltv", float("inf")),
        ("cltv", -1.0),
        ("dscr", float("nan")),
        ("risk_score", 101.0),
        ("risk_score", -1.0),
        ("fico_score", 900),
        ("fico_score", True),
    ],
)
def test_decision_agent_suspends_on_invalid_metrics(
    valid_assessment, field, invalid_value
):
    valid_assessment[field] = invalid_value

    result = DecisionAgent().evaluate(valid_assessment)

    assert result["recommendation"] == "SUSPEND"
    assert result["requires_human_review"] is True
    assert result["reasons"]


@pytest.mark.parametrize(
    "confidence",
    [float("nan"), float("inf"), -0.1, 1.1, True],
)
def test_decision_agent_rejects_invalid_confidence(
    valid_assessment, confidence
):
    valid_assessment["confidence"] = confidence

    with pytest.raises(ValueError, match="confidence must be a number"):
        DecisionAgent().evaluate(valid_assessment)


@pytest.mark.parametrize(
    "field",
    ["dti_percentage", "ltv", "cltv", "dscr", "risk_score"],
)
def test_boolean_numeric_metric_is_rejected(valid_assessment, field):
    valid_assessment[field] = True

    result = DecisionAgent().evaluate(valid_assessment)

    assert result["recommendation"] == "SUSPEND"
    assert result["requires_human_review"] is True
    assert any(
        f"{field} must be numeric." in reason
        for reason in result["reasons"]
    )


def test_extremely_large_numeric_metric_is_suspended(valid_assessment):
    valid_assessment["dti_percentage"] = 10**10000

    result = DecisionAgent().evaluate(valid_assessment)

    assert result["recommendation"] == "SUSPEND"
    assert result["requires_human_review"] is True


def test_policy_review_outcome_requires_human_review(valid_assessment):
    valid_assessment["policy_outcome"] = "review"

    result = DecisionAgent().evaluate(valid_assessment)

    assert result["recommendation"] == "SUSPEND"
    assert result["requires_human_review"] is True
    assert any(
        "requires further review" in reason
        for reason in result["reasons"]
    )


def test_data_conflicts_require_human_review(valid_assessment):
    valid_assessment["data_conflicts"] = True

    result = DecisionAgent().evaluate(valid_assessment)

    assert result["recommendation"] == "SUSPEND"
    assert result["requires_human_review"] is True
    assert any(
        "conflicts" in reason.lower()
        for reason in result["reasons"]
    )


def test_unhashable_policy_outcome_raises_value_error(valid_assessment):
    valid_assessment["policy_outcome"] = ["pass"]

    with pytest.raises(ValueError, match="policy_outcome"):
        DecisionAgent().evaluate(valid_assessment)


def test_extremely_large_confidence_raises_value_error(valid_assessment):
    valid_assessment["confidence"] = 10**10000

    with pytest.raises(
        ValueError,
        match="confidence must be a number",
    ):
        DecisionAgent().evaluate(valid_assessment)
