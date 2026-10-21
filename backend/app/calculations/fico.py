
"""FICO score validation and qualifying-score selection."""

from typing import Sequence


def determine_qualifying_fico(scores: Sequence[int]) -> int:

    if isinstance(scores, (str, bytes)) or not isinstance(scores, Sequence):
        raise ValueError("scores must be a sequence of FICO scores.")

    if not 1 <= len(scores) <= 3:
        raise ValueError("Provide between one and three FICO scores.")

    for score in scores:
        if isinstance(score, bool) or not isinstance(score, int):
            raise ValueError("Each FICO score must be an integer.")
        if not 300 <= score <= 850:
            raise ValueError("Each FICO score must be between 300 and 850.")

    sorted_scores = sorted(scores)

    if len(sorted_scores) == 1:
        return sorted_scores[0]

    if len(sorted_scores) == 2:
        return sorted_scores[0]

    return sorted_scores[1]
