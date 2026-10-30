"""LTV-001: loan-to-value check against a reviewed band table."""

from __future__ import annotations

from typing import Any

from app.compliance.config import RuleSettings
from app.compliance.rules.base import (
    CheckResult,
    ComplianceContext,
    as_number,
    cannot_verify,
    no_issue,
    potential_issue,
)
from app.compliance.schemas import Severity


class LTVRule:
    rule_id = "LTV-001"
    requirement = "Loan-to-value ratio is within the applicable reviewed limit"
    required_inputs = ("loan_amount", "property_value")
    evidence_query = (
        "RBI housing loan loan-to-value LTV ratio prudential limit property value"
    )
    requires_config = True

    def check(self, ctx: ComplianceContext, settings: RuleSettings) -> CheckResult:
        if not settings.verified:
            return cannot_verify(
                "no reviewed LTV band table is configured for LTV-001.",
                [f"verified LTV bands from retrieved text ({settings.source_ref})"],
            )

        bands = _parse_bands(settings.values.get("bands"))
        if not bands:
            return cannot_verify(
                "the configured LTV band table is empty or malformed.",
                [f"valid LTV bands from reviewed configuration ({settings.source_ref})"],
            )

        loan_amount = as_number(ctx.resolve("loan_amount"))
        property_value = as_number(ctx.resolve("property_value"))
        if loan_amount is None or property_value is None:
            return cannot_verify(
                "loan amount or property value is not numeric.",
                ["numeric loan amount and property value"],
            )
        if loan_amount <= 0 or property_value <= 0:
            return cannot_verify(
                "loan amount or property value is not positive.",
                ["positive loan amount and property value"],
            )

        band = _select_band(bands, loan_amount)
        if band is None:
            return cannot_verify(
                "no configured LTV band covers the supplied loan amount.",
                ["an LTV band covering the supplied loan amount"],
            )

        ltv_percent = (loan_amount / property_value) * 100.0
        max_ltv = band["max_ltv_percent"]
        assert max_ltv is not None
        if ltv_percent > max_ltv + 0.01:
            return potential_issue(
                f"LTV is {ltv_percent:.2f}% but the reviewed limit for this loan "
                f"amount is {max_ltv:.2f}%.",
                Severity.HIGH,
            )
        return no_issue(
            f"LTV is {ltv_percent:.2f}% against a reviewed limit of {max_ltv:.2f}%."
        )


def _parse_bands(value: Any) -> list[dict[str, float | None]]:
    if not isinstance(value, list):
        return []
    bands: list[dict[str, float | None]] = []
    for item in value:
        if not isinstance(item, dict):
            return []
        max_loan = item.get("max_loan_amount")
        max_ltv = as_number(item.get("max_ltv_percent"))
        if max_ltv is None or max_ltv <= 0:
            return []
        if max_loan is not None:
            parsed_max_loan = as_number(max_loan)
            if parsed_max_loan is None or parsed_max_loan <= 0:
                return []
            bands.append(
                {"max_loan_amount": parsed_max_loan, "max_ltv_percent": max_ltv}
            )
        else:
            bands.append({"max_loan_amount": None, "max_ltv_percent": max_ltv})
    return bands


def _select_band(
    bands: list[dict[str, float | None]], loan_amount: float
) -> dict[str, float | None] | None:
    for band in bands:
        max_loan = band["max_loan_amount"]
        if max_loan is None or loan_amount <= max_loan:
            return band
    return None
