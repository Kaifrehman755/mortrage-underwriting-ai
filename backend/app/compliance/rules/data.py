"""DATA-001: source freshness and index-coverage check (system evidence)."""

from __future__ import annotations

from app.compliance.config import RuleSettings
from app.compliance.rules.base import (
    CheckResult,
    ComplianceContext,
    _parse_date,
    as_int,
    cannot_verify,
    no_issue,
)


class DataSourceRule:
    rule_id = "DATA-001"
    requirement = (
        "The source used by the case is fresh, its effective window covers the "
        "loan date, and the active index version is the version used"
    )
    required_inputs = (
        "source_last_success_at",
        "index_version",
        "active_index_version",
    )
    evidence_query = None  # System check; the engine supplies registry evidence.
    requires_config = True

    def check(self, ctx: ComplianceContext, settings: RuleSettings) -> CheckResult:
        max_age_days = as_int(settings.values.get("max_source_age_days"))
        if not settings.verified or max_age_days is None or max_age_days <= 0:
            return cannot_verify(
                "no reviewed source-freshness threshold is configured for DATA-001.",
                [
                    "verified maximum source age from reviewed policy "
                    f"({settings.source_ref})"
                ],
            )

        as_of = ctx.as_of_date()
        if as_of is None:
            return cannot_verify(
                "the loan date is missing or not ISO formatted.",
                ["valid loan date"],
            )

        last_success = _parse_date(ctx.resolve("source_last_success_at"))
        if last_success is None:
            return cannot_verify(
                "the source's last-success timestamp is missing or not a date.",
                ["source_last_success_at timestamp"],
            )

        age_days = (as_of - last_success).days
        if age_days < 0:
            return cannot_verify(
                "the source's last-success timestamp is after the loan date.",
                ["source refresh timestamp that is not in the future"],
            )
        if age_days > max_age_days:
            return cannot_verify(
                f"the source was last refreshed {age_days} days before the loan "
                f"date, beyond the reviewed {max_age_days}-day limit.",
                ["a source refresh inside the reviewed freshness window"],
            )

        index_version = ctx.resolve("index_version")
        active_index_version = ctx.resolve("active_index_version")
        if str(index_version) != str(active_index_version):
            return cannot_verify(
                "the index version used by the case is not the active index version.",
                ["matching index and active index versions"],
            )

        effective_to = _parse_date(ctx.resolve("source_effective_to"))
        if effective_to is not None and as_of > effective_to:
            return cannot_verify(
                "the source's effective window ends before the loan date.",
                ["source effective window that covers the loan date"],
            )

        return no_issue(
            f"The source was refreshed {age_days} days before the loan date and "
            "the active index version is in use."
        )
