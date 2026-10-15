
import pytest

from app.agents.credit_agent import CreditAgent


def test_credit_agent_analyzes_valid_fico():
    agent = CreditAgent()

    result = agent.analyze(740)

    assert result["agent"] == "credit_analysis"
    assert result["status"] == "completed"
    assert result["credit_analysis"]["fico_score"] == 740
    assert result["credit_analysis"]["credit_category"] == "Very Good"
    assert result["credit_analysis"]["warnings"] == []


def test_credit_agent_preserves_low_score_warning():
    agent = CreditAgent()

    result = agent.analyze(580)

    assert result["credit_analysis"]["credit_category"] == "Fair"
    assert len(result["credit_analysis"]["warnings"]) == 1


def test_credit_agent_rejects_invalid_fico():
    agent = CreditAgent()

    with pytest.raises(ValueError):
        agent.analyze(900)
