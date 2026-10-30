"""TITLE-001: title, encumbrance and CERSAI check presence."""

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


class TitleRule:
    rule_id = "TITLE-001"
    requirement = (
        "Title documents, an encumbrance certificate and a CERSAI check are "
        "present in the case file"
    )
    required_inputs = (
        "title_document_present",
        "encumbrance_certificate_present",
        "cersai_check_present",
    )
    evidence_query = (
        "SARFAESI CERSAI registration title documents encumbrance certificate "
        "mortgage charge"
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
                "one or more title-status fields is missing or not boolean.",
                [
                    f"boolean {name}"
                    for name, value in values.items()
                    if value is None
                ],
            )

        absent = [name for name, value in values.items() if value is False]
        if absent:
            return potential_issue(
                "the following required title checks are marked absent: "
                + format_names(absent)
                + ".",
                Severity.HIGH,
            )
        return no_issue("All required title, encumbrance and CERSAI checks are marked present.")
