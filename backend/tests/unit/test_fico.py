"""Unit tests for the deterministic FICO mid-score rule."""

import pytest

from app.calculations.fico import determine_qualifying_fico


@pytest.mark.parametrize(
    ("scores", "expected"),
    [
        ([720, 680, 700], 700),  # three bureaus -> middle score
        ([800, 750], 750),  # two bureaus -> lower score
        ([690], 690),  # one bureau -> that score
        ([700, 700, 700], 700),  # ties are stable
    ],
)
def test_mid_score_rule(scores: list[int], expected: int) -> None:
    assert determine_qualifying_fico(scores) == expected


def test_empty_scores_rejected() -> None:
    with pytest.raises(ValueError, match="At least one FICO score"):
        determine_qualifying_fico([])


@pytest.mark.parametrize("score", [299, 851, -1])
def test_out_of_range_rejected(score: int) -> None:
    with pytest.raises(ValueError, match="between 300 and 850"):
        determine_qualifying_fico([score])


@pytest.mark.parametrize("score", [True, "700", 700.0])
def test_non_integer_rejected(score: object) -> None:
    with pytest.raises(ValueError, match="must be integers"):
        determine_qualifying_fico([score])
