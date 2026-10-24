"""Deterministic FICO score interpretation and qualification tiering (Reserved for Phase 1+)."""

FICO_MIN = 300
FICO_MAX = 850


def determine_qualifying_fico(scores: list) -> int:
    """Determine the representative qualifying credit score using the mid-score rule.

    Mortgage underwriting convention:

    * three scores -> the middle (median) score;
    * two scores   -> the lower score;
    * one score    -> that score.

    Raises:
        ValueError: if no scores are supplied, a score is not an integer, or a
            score falls outside the valid FICO range.
    """
    if not scores:
        raise ValueError("At least one FICO score is required.")

    normalized: list[int] = []
    for score in scores:
        if isinstance(score, bool) or not isinstance(score, int):
            raise ValueError("FICO scores must be integers.")
        if not FICO_MIN <= score <= FICO_MAX:
            raise ValueError(
                f"FICO scores must be between {FICO_MIN} and {FICO_MAX}."
            )
        normalized.append(score)

    ordered = sorted(normalized)
    # Mid-score rule: median for three, lower of two, the only score for one.
    return ordered[(len(ordered) - 1) // 2]
