from typing import Any


def calculate_credit_analysis(fico_score: int) -> dict[str, Any]:
    """
    Validate a FICO score and classify its credit-score range.

    This is an indicative classification, not a mortgage approval decision.
    """
    if isinstance(fico_score, bool) or not isinstance(fico_score, int):
        raise ValueError("FICO score must be an integer.")

    if not 300 <= fico_score <= 850:
        raise ValueError("FICO score must be between 300 and 850.")

    if fico_score < 580:
        category = "Poor"
    elif fico_score < 670:
        category = "Fair"
    elif fico_score < 740:
        category = "Good"
    elif fico_score < 800:
        category = "Very Good"
    else:
        category = "Exceptional"

    warnings: list[str] = []

    if fico_score < 620:
        warnings.append(
            "FICO score is below 620; additional underwriting review may be needed."
        )

    return {
        "fico_score": fico_score,
        "credit_category": category,
        "warnings": warnings,
    }
