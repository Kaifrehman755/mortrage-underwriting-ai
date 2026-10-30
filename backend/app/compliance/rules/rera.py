"""RERA-001: project registration and RERA identifier for under-construction cases."""

from __future__ import annotations

import re

from app.compliance.config import RuleSettings
from app.compliance.rules.base import (
    CheckResult,
    ComplianceContext,
    as_bool,
    cannot_verify,
    no_issue,
    potential_issue,
)
from app.compliance.schemas import Severity


class RERARule:
    rule_id = "RERA-001"
    requirement = (
        "An under-construction project is registered under RERA and carries a "
        "valid RERA identifier"
    )
    required_inputs = ("under_construction", "project_registered")
    evidence_query = (
        "RERA Act 2016 project registration under-construction project RERA "
        "registration number"
    )
    requires_config = False

    def check(self, ctx: ComplianceContext, settings: RuleSettings) -> CheckResult:
        under_construction = as_bool(ctx.resolve("under_construction"))
        project_registered = as_bool(ctx.resolve("project_registered"))

        if under_construction is None or project_registered is None:
            return cannot_verify(
                "under-construction status or project-registration status is missing "
                "or not boolean.",
                ["boolean under_construction and project_registered values"],
            )

        if not under_construction:
            return no_issue(
                "The case is not marked as under construction, so this rule's "
                "registration check is not required."
            )

        if not project_registered:
            return potential_issue(
                "the project is marked under construction but not registered.",
                Severity.HIGH,
            )

        rera_id = ctx.resolve("rera_id")
        if rera_id is None or (isinstance(rera_id, str) and not rera_id.strip()):
            return cannot_verify(
                "the project is under construction and registered, but no RERA "
                "identifier was supplied.",
                ["RERA identifier for the under-construction project"],
            )

        pattern = settings.values.get("rera_id_pattern")
        if settings.verified and isinstance(pattern, str) and pattern:
            try:
                matches = re.fullmatch(pattern, str(rera_id).strip()) is not None
            except re.error:
                return cannot_verify(
                    "the configured RERA identifier pattern is invalid.",
                    [f"valid RERA identifier pattern ({settings.source_ref})"],
                )
            if not matches:
                return potential_issue(
                    "the RERA identifier does not match the reviewed state pattern.",
                    Severity.MEDIUM,
                )

        return no_issue("The under-construction project is marked registered with a RERA identifier.")
