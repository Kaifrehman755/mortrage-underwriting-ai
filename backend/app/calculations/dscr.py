
"""Debt Service Coverage Ratio (DSCR) calculation."""

from decimal import Decimal
from typing import Any

from app.calculations.validation import to_finite_decimal


def calculate_dscr(
    net_operating_income: Decimal,
    annual_debt_service: Decimal,
) -> dict[str, Any]:
    """
    Calculate the Debt Service Coverage Ratio.

    Formula:
        DSCR = Net Operating Income / Annual Debt Service
    """
    net_operating_income = to_finite_decimal(
        net_operating_income, "Net operating income"
    )
    annual_debt_service = to_finite_decimal(
        annual_debt_service, "Annual debt service"
    )

    if net_operating_income < 0:
        raise ValueError("Net operating income cannot be negative.")

    if annual_debt_service < 0:
        raise ValueError("Annual debt service cannot be negative.")

    if annual_debt_service == 0:
        raise ValueError("Annual debt service must be greater than zero.")

    dscr = net_operating_income / annual_debt_service

    warnings: list[str] = []
    if dscr < Decimal("1.0"):
        warnings.append("DSCR is below 1.0; income does not cover debt service.")
    elif dscr < Decimal("1.25"):
        warnings.append(
            "DSCR is below the illustrative 1.25 underwriting benchmark."
        )

    return {
        "net_operating_income": net_operating_income,
        "annual_debt_service": annual_debt_service,
        "dscr": dscr.quantize(Decimal("0.01")),
        "warnings": warnings,
    }
