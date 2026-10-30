"""KYC-001: customer due-diligence status without storing identifiers."""

from __future__ import annotations

from app.compliance.config import RuleSettings
from app.compliance.rules.base import (
    CheckResult,
    ComplianceContext,
    as_bool,
    cannot_verify,
    format_names,
    no_issue,
    potential_issue,
)
from app.compliance.schemas import Severity


class KYCRule:
    rule_id = "KYC-001"
    requirement = (
        "KYC and customer due diligence are marked complete, including PAN "
        "verification status; raw identifiers are not stored in the case"
    )
    required_inputs = (
        "kyc_completed",
        "customer_due_diligence_completed",
        "pan_verified",
    )
    evidence_query = (
        "RBI KYC Master Direction customer due diligence PAN officially valid "
        "document verification"
    )
    requires_config = False

    def check(self, ctx: ComplianceContext, settings: RuleSettings) -> CheckResult:
        del settings  # This rule has no numeric threshold.
        values = {
            name: as_bool(ctx.resolve(name))
            for name in self.required_inputs
        }
        if any(value is None for value in values.values()):
            return cannot_verify(
                "one or more KYC status fields is missing or not boolean.",
                [
                    f"boolean {name}"
                    for name, value in values.items()
                    if value is None
                ],
            )

        incomplete = [name for name, value in values.items() if value is False]
        if incomplete:
            return potential_issue(
                "the following KYC checks are not marked complete: "
                + format_names(incomplete)
                + ".",
                Severity.HIGH,
            )
        return no_issue(
            "KYC, customer due diligence and PAN verification are marked complete."
        )
