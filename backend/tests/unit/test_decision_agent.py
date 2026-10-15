
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
    agent = DecisionAgent()

    result = agent.evaluate(valid_assessment)

    assert result["recommendation"] == "APPROVE"
    assert result["requires_human_review"] is False


def test_decision_agent_suspends_when_documents_missing(valid_assessment):
    agent = DecisionAgent()
    valid_assessment["documents_complete"] = False

    result = agent.evaluate(valid_assessment)

    assert result["recommendation"] == "SUSPEND"
    assert result["requires_human_review"] is True
    assert any("documents" in reason for reason in result["reasons"])


def test_decision_agent_suspends_when_confidence_is_low(valid_assessment):
    agent = DecisionAgent()
    valid_assessment["confidence"] = 0.60

    result = agent.evaluate(valid_assessment)

    assert result["recommendation"] == "SUSPEND"
    assert result["requires_human_review"] is True


def test_decision_agent_denies_policy_fail(valid_assessment):
    agent = DecisionAgent()
    valid_assessment["policy_outcome"] = "fail"

    result = agent.evaluate(valid_assessment)

    assert result["recommendation"] == "DENY"
    assert result["requires_human_review"] is False


def test_decision_agent_suspends_when_data_is_missing(valid_assessment):
    agent = DecisionAgent()
    del valid_assessment["fico_score"]

    result = agent.evaluate(valid_assessment)

    assert result["recommendation"] == "SUSPEND"
    assert result["requires_human_review"] is True
    assert any("fico_score" in reason for reason in result["reasons"])


def test_decision_agent_rejects_invalid_policy_outcome(valid_assessment):
    agent = DecisionAgent()
    valid_assessment["policy_outcome"] = "unknown"

    with pytest.raises(ValueError):
        agent.evaluate(valid_assessment)
