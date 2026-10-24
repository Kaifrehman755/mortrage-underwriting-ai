"""Deterministic composite risk scoring engine."""

import math


def compute_composite_risk_score(
    dti: float,
    ltv: float,
    fico: int,
    reserves_months: float,
) -> float:
    """
    Calculate a composite mortgage risk score from 0 to 100.

    Higher scores indicate higher risk.

    Inputs:
        dti: Debt-to-income ratio expressed as a percentage.
        ltv: Loan-to-value ratio expressed as a percentage.
        fico: FICO score, from 300 to 850.
        reserves_months: Months of available cash reserves.

    Returns:
        Composite risk score rounded to two decimal places.
    """
    if isinstance(dti, bool) or not isinstance(dti, (int, float)):
        raise ValueError("DTI must be a numeric percentage.")

    if not math.isfinite(dti) or dti < 0:
        raise ValueError("DTI must be a finite, non-negative percentage.")

    if isinstance(ltv, bool) or not isinstance(ltv, (int, float)):
        raise ValueError("LTV must be a numeric percentage.")

    if not math.isfinite(ltv) or ltv < 0:
        raise ValueError("LTV must be a finite, non-negative percentage.")

    if isinstance(fico, bool) or not isinstance(fico, int):
        raise ValueError("FICO must be an integer.")

    if not 300 <= fico <= 850:
        raise ValueError("FICO must be between 300 and 850.")

    if (
        isinstance(reserves_months, bool)
        or not isinstance(reserves_months, (int, float))
    ):
        raise ValueError("Reserves must be numeric.")

    if not math.isfinite(reserves_months) or reserves_months < 0:
        raise ValueError("Reserves must be finite and non-negative.")

    # DTI risk: maximum 30 points.
    if dti <= 20:
        dti_risk = 0
    elif dti <= 36:
        dti_risk = 8
    elif dti <= 43:
        dti_risk = 18
    elif dti <= 50:
        dti_risk = 25
    else:
        dti_risk = 30

    # LTV risk: maximum 25 points.
    if ltv <= 60:
        ltv_risk = 0
    elif ltv <= 80:
        ltv_risk = 8
    elif ltv <= 90:
        ltv_risk = 16
    elif ltv <= 97:
        ltv_risk = 22
    else:
        ltv_risk = 25

    # FICO risk: maximum 30 points.
    if fico >= 800:
        fico_risk = 0
    elif fico >= 740:
        fico_risk = 6
    elif fico >= 670:
        fico_risk = 15
    elif fico >= 580:
        fico_risk = 24
    else:
        fico_risk = 30

    # Cash reserve risk: maximum 15 points.
    if reserves_months >= 12:
        reserves_risk = 0
    elif reserves_months >= 6:
        reserves_risk = 4
    elif reserves_months >= 3:
        reserves_risk = 9
    elif reserves_months >= 1:
        reserves_risk = 12
    else:
        reserves_risk = 15

    total_risk = (
        dti_risk
        + ltv_risk
        + fico_risk
        + reserves_risk
    )

    return round(float(total_risk), 2)
