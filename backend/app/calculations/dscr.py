from decimal import Decimal
from typing import Any


def calculate_dscr(
    net_operating_income: Decimal,
    annual_debt_service: Decimal,
) -> dict[str, Any]:
    """
    Calculate the Debt Service Coverage Ratio (DSCR).

    Formula:
        DSCR = Net Operating Income / Annual Debt Service
    """
    warnings: list[str] = []

    if net_operating_income < 0:
        raise ValueError("Net operating income cannot be negative.")

    if annual_debt_service < 0:
        raise ValueError("Annual debt service cannot be negative.")

    if annual_debt_service == 0:
        raise ValueError("Annual debt service must be greater than zero.")

    dscr = net_operating_income / annual_debt_service

    if dscr < Decimal("1.0"):
        warnings.append("DSCR is below 1.0; income does not cover debt service.")
    elif dscr < Decimal("1.25"):
        warnings.append("DSCR is below the illustrative 1.25 underwriting benchmark.")

    return {
        "net_operating_income": net_operating_income,
        "annual_debt_service": annual_debt_service,
        "dscr": dscr.quantize(Decimal("0.01")),
        "warnings": warnings,
    }
