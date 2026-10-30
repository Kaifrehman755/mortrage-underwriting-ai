"""KFS-001: Key Fact Statement fields and internal consistency."""

from __future__ import annotations

from app.compliance.config import RuleSettings
from app.compliance.rules.base import (
    CheckResult,
    ComplianceContext,
    as_int,
    as_number,
    cannot_verify,
    no_issue,
    potential_issue,
)
from app.compliance.schemas import Severity


class KFSRule:
    rule_id = "KFS-001"
    requirement = (
        "Key Fact Statement fields are present and internally consistent, "
        "including APR and the cooling-off period"
    )
    required_inputs = (
        "loan_amount",
        "annual_interest_rate",
        "tenure_months",
        "apr",
        "cooling_off_days",
    )
    evidence_query = (
        "RBI Key Fact Statement KFS APR annual percentage rate cooling-off period "
        "required disclosures"
    )
    requires_config = True

    def check(self, ctx: ComplianceContext, settings: RuleSettings) -> CheckResult:
        min_cooling_off_days = as_int(settings.values.get("min_cooling_off_days"))
        if not settings.verified or min_cooling_off_days is None:
            return cannot_verify(
                "no reviewed cooling-off threshold is configured for KFS-001.",
                [
                    "verified KFS cooling-off threshold from retrieved text "
                    f"({settings.source_ref})"
                ],
            )

        loan_amount = as_number(ctx.resolve("loan_amount"))
        interest_rate = as_number(ctx.resolve("annual_interest_rate"))
        tenure_months = as_int(ctx.resolve("tenure_months"))
        apr = as_number(ctx.resolve("apr"))
        cooling_off_days = as_int(ctx.resolve("cooling_off_days"))

        if (
            loan_amount is None
            or interest_rate is None
            or tenure_months is None
            or apr is None
            or cooling_off_days is None
        ):
            return cannot_verify(
                "one or more KFS fields are present but not numeric or integral.",
                ["numeric loan amount, interest rate, tenure, APR and cooling-off days"],
            )

        issues: list[str] = []
        if loan_amount <= 0:
            issues.append("loan amount is not positive")
        if interest_rate < 0:
            issues.append("annual interest rate is negative")
        if tenure_months <= 0:
            issues.append("tenure is not positive")
        if apr < 0:
            issues.append("APR is negative")
        if apr + 0.0001 < interest_rate:
            issues.append("APR is lower than the stated annual interest rate")
        if cooling_off_days < min_cooling_off_days:
            issues.append(
                f"cooling-off period ({cooling_off_days} days) is below the reviewed "
                f"minimum ({min_cooling_off_days} days)"
            )

        if issues:
            return potential_issue(
                "KFS fields need review: " + "; ".join(issues) + ".",
                Severity.MEDIUM,
            )
        return no_issue("KFS fields are present and internally consistent.")
