"""VAL-001: valuation credentials and gap against the model estimate."""

from __future__ import annotations

from app.compliance.config import RuleSettings
from app.compliance.rules.base import (
    CheckResult,
    ComplianceContext,
    as_bool,
    as_number,
    cannot_verify,
    no_issue,
    potential_issue,
)
from app.compliance.schemas import Severity


class ValuationRule:
    rule_id = "VAL-001"
    requirement = (
        "The valuation report is prepared by an empanelled valuer and its value "
        "is reconciled with the model estimate and any supplied circle rate"
    )
    required_inputs = (
        "valuer_empanelled",
        "valuation_report_present",
        "valuation_amount",
        "model_estimate",
    )
    evidence_query = (
        "IBBI registered valuer valuation report empanelled valuer valuation "
        "standards circle rate"
    )
    requires_config = True

    def check(self, ctx: ComplianceContext, settings: RuleSettings) -> CheckResult:
        empanelled = as_bool(ctx.resolve("valuer_empanelled"))
        report_present = as_bool(ctx.resolve("valuation_report_present"))
        if empanelled is None or report_present is None:
            return cannot_verify(
                "valuer-empanelment or valuation-report status is missing or not "
                "boolean.",
                ["boolean valuer_empanelled and valuation_report_present values"],
            )
        if not empanelled or not report_present:
            return potential_issue(
                "the valuation report is missing or the valuer is not marked as "
                "empanelled.",
                Severity.HIGH,
            )

        valuation_amount = as_number(ctx.resolve("valuation_amount"))
        model_estimate = as_number(ctx.resolve("model_estimate"))
        if valuation_amount is None or model_estimate is None:
            return cannot_verify(
                "valuation amount or model estimate is not numeric.",
                ["numeric valuation_amount and model_estimate"],
            )
        if valuation_amount <= 0 or model_estimate <= 0:
            return cannot_verify(
                "valuation amount or model estimate is not positive.",
                ["positive valuation_amount and model_estimate"],
            )

        max_model_gap = as_number(settings.values.get("max_model_gap_percent"))
        if not settings.verified or max_model_gap is None:
            return cannot_verify(
                "no reviewed model-gap threshold is configured for VAL-001.",
                [
                    "verified valuation gap threshold from retrieved text "
                    f"({settings.source_ref})"
                ],
            )
        if max_model_gap < 0:
            return cannot_verify(
                "the configured model-gap threshold is negative.",
                [f"valid model-gap threshold ({settings.source_ref})"],
            )

        issues: list[str] = []
        model_gap = abs(valuation_amount - model_estimate) / model_estimate * 100.0
        if model_gap > max_model_gap:
            issues.append(
                f"valuation differs from the model estimate by {model_gap:.2f}% "
                f"(reviewed limit {max_model_gap:.2f}%)"
            )

        circle_rate = as_number(ctx.resolve("circle_rate_value"))
        max_circle_gap = as_number(settings.values.get("max_circle_rate_gap_percent"))
        if circle_rate is not None:
            if circle_rate <= 0:
                return cannot_verify(
                    "the supplied circle rate is not positive.",
                    ["positive circle_rate_value"],
                )
            if max_circle_gap is None:
                return cannot_verify(
                    "a circle rate was supplied but no reviewed circle-rate gap "
                    "threshold is configured.",
                    [
                        "verified circle-rate gap threshold from retrieved text "
                        f"({settings.source_ref})"
                    ],
                )
            circle_gap = abs(valuation_amount - circle_rate) / circle_rate * 100.0
            if circle_gap > max_circle_gap:
                issues.append(
                    f"valuation differs from the circle rate by {circle_gap:.2f}% "
                    f"(reviewed limit {max_circle_gap:.2f}%)"
                )

        if issues:
            return potential_issue(
                "valuation reconciliation needs review: " + "; ".join(issues) + ".",
                Severity.MEDIUM,
            )
        return no_issue(
            "The valuer is marked empanelled and the valuation is within the "
            "reviewed reconciliation thresholds."
        )
