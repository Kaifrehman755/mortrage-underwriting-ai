
import pytest

from app.calculations.fico import determine_qualifying_fico


def test_single_fico_score():
    assert determine_qualifying_fico([740]) == 740


def test_two_scores_selects_lower_score():
    assert determine_qualifying_fico([720, 680]) == 680


def test_three_scores_selects_middle_score():
    assert determine_qualifying_fico([720, 680, 750]) == 720


def test_scores_are_sorted_before_selection():
    assert determine_qualifying_fico([850, 300, 700]) == 700


@pytest.mark.parametrize("scores", [[], [700, 720, 740, 760]])
def test_rejects_invalid_number_of_scores(scores):
    with pytest.raises(ValueError):
        determine_qualifying_fico(scores)


@pytest.mark.parametrize("score", [True, False, 299, 851, 700.5, "740", None])
def test_rejects_invalid_scores(score):
    with pytest.raises(ValueError):
        determine_qualifying_fico([score])


@pytest.mark.parametrize("scores", ["740", b"740", None])
def test_rejects_invalid_score_containers(scores):
    with pytest.raises(ValueError):
        determine_qualifying_fico(scores)
