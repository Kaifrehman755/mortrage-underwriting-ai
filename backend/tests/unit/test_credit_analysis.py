import pytest

from backend.app.calculations.credit_analysis import (
    calculate_credit_analysis,
)


def test_credit_analysis_poor_score():
    result = calculate_credit_analysis(550)

    assert result["credit_category"] == "Poor"
    assert len(result["warnings"]) == 1


def test_credit_analysis_fair_score():
    result = calculate_credit_analysis(620)

    assert result["credit_category"] == "Fair"
    assert result["warnings"] == []


def test_credit_analysis_good_score():
    result = calculate_credit_analysis(700)

    assert result["credit_category"] == "Good"
    assert result["warnings"] == []


def test_credit_analysis_very_good_score():
    result = calculate_credit_analysis(760)

    assert result["credit_category"] == "Very Good"
    assert result["warnings"] == []


def test_credit_analysis_exceptional_score():
    result = calculate_credit_analysis(820)

    assert result["credit_category"] == "Exceptional"
    assert result["warnings"] == []


def test_credit_analysis_minimum_score():
    result = calculate_credit_analysis(300)

    assert result["credit_category"] == "Poor"


def test_credit_analysis_maximum_score():
    result = calculate_credit_analysis(850)

    assert result["credit_category"] == "Exceptional"


@pytest.mark.parametrize("score", [299, 851, -1, 1000])
def test_credit_analysis_invalid_score_range(score):
    with pytest.raises(ValueError, match="between 300 and 850"):
        calculate_credit_analysis(score)


@pytest.mark.parametrize("score", [75.5, "700", True, None])
def test_credit_analysis_invalid_score_type(score):
    with pytest.raises(ValueError, match="must be an integer"):
        calculate_credit_analysis(score)
