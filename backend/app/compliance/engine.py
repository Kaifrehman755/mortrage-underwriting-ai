"""Deterministic compliance rule engine.

The engine orchestrates rules but deliberately has no LLM in the loop. Each rule
returns a status plus an evidence query. The engine attaches retrieved evidence,
downgrades every unevidenced flag to ``cannot_verify``, and fails closed when
retrieval is empty or raises.
"""

from __future__ import annotations

import json
import logging
from typing import Protocol
from uuid import UUID

from app.compliance.config import ComplianceConfig
from app.compliance.rules.base import ComplianceContext, ComplianceRule
from app.compliance.schemas import (
    ComplianceOutput,
    ComplianceRun,
    ComplianceStatus,
    Severity,
)
from app.rag.schemas import EvidenceItem

logger = logging.getLogger(__name__)


class EvidenceRetriever(Protocol):
    """Minimal retrieval interface used by the engine."""

    def retrieve(
        self,
        query: str,
        state_code: str | None = None,
        loan_date: str | None = None,
        top_k: int = 5,
        threshold: float | None = None,
    ) -> list[EvidenceItem]:
        """Return evidence relevant to the query, or an empty list."""
        ...


class NullEvidenceRetriever:
    """Safe default: return no evidence, which forces ``cannot_verify``."""

    def retrieve(
        self,
        query: str,
        state_code: str | None = None,
        loan_date: str | None = None,
        top_k: int = 5,
        threshold: float | None = None,
    ) -> list[EvidenceItem]:
        del query, state_code, loan_date, top_k, threshold
        return []


class ComplianceEngine:
    """Run a rule pack against one case context."""

    def __init__(
        self,
        rules: list[ComplianceRule] | None = None,
        retriever: EvidenceRetriever | None = None,
        config: ComplianceConfig | None = None,
    ):
        from app.compliance.rules import default_rules

        self.rules = rules if rules is not None else default_rules()
        self.retriever = retriever or NullEvidenceRetriever()
        self.config = config or ComplianceConfig.load()

    def run(self, ctx: ComplianceContext) -> ComplianceRun:
        """Evaluate every rule and attach evidence where a finding is non-abstain."""
        findings: list[ComplianceOutput] = []
        evidence_by_id: dict[str, EvidenceItem] = {}

        for rule in self.rules:
            settings = self.config.for_rule(rule.rule_id)

            if not ctx.loan_date:
                findings.append(
                    self._finding(
                        ctx,
                        rule,
                        status=ComplianceStatus.CANNOT_VERIFY,
                        explanation=(
                            "Cannot verify: the loan date is missing, so the rule "
                            "cannot be applied as of the loan date. Human review required."
                        ),
                        missing_information=["loan_date"],
                    )
                )
                continue

            missing = ctx.missing(rule.required_inputs)
            if missing:
                findings.append(
                    self._finding(
                        ctx,
                        rule,
                        status=ComplianceStatus.CANNOT_VERIFY,
                        explanation=(
                            "Cannot verify: required input(s) missing: "
                            + ", ".join(missing)
                            + ". Human review required."
                        ),
                        missing_information=[f"required input: {name}" for name in missing],
                    )
                )
                continue

            try:
                result = rule.check(ctx, settings)
            except Exception as exc:  # noqa: BLE001 - fail closed at rule boundary
                logger.exception("Compliance rule %s failed", rule.rule_id)
                findings.append(
                    self._finding(
                        ctx,
                        rule,
                        status=ComplianceStatus.CANNOT_VERIFY,
                        explanation=(
                            "Cannot verify: rule evaluation failed and was not "
                            "retried. Human review required."
                        ),
                        missing_information=[
                            f"rule evaluation result for {rule.rule_id}",
                            f"error type: {type(exc).__name__}",
                        ],
                    )
                )
                continue

            if result.status is ComplianceStatus.CANNOT_VERIFY:
                findings.append(
                    self._finding(
                        ctx,
                        rule,
                        status=result.status,
                        explanation=result.explanation,
                        missing_information=result.missing_information,
                        severity=result.severity,
                    )
                )
                continue

            evidence = self._retrieve_evidence(rule, ctx)
            if not evidence:
                findings.append(
                    self._finding(
                        ctx,
                        rule,
                        status=ComplianceStatus.CANNOT_VERIFY,
                        explanation=(
                            "Cannot verify: no relevant approved evidence was "
                            "retrieved for this rule. Human review required."
                        ),
                        missing_information=[
                            f"approved evidence for {rule.rule_id}: {rule.evidence_query or 'system check'}"
                        ],
                    )
                )
                continue

            for item in evidence:
                evidence_by_id[item.evidence_id] = item

            findings.append(
                self._finding(
                    ctx,
                    rule,
                    status=result.status,
                    explanation=result.explanation,
                    missing_information=result.missing_information,
                    severity=result.severity,
                    evidence_refs=[UUID(item.evidence_id) for item in evidence],
                )
            )

        missing_information: list[str] = []
        for finding in findings:
            for missing_item in finding.missing_information:
                if missing_item not in missing_information:
                    missing_information.append(missing_item)

        return ComplianceRun(
            case_id=ctx.case_id,
            rule_set_version=self.config.rule_set_version,
            findings=findings,
            evidence=list(evidence_by_id.values()),
            missing_information=missing_information,
            human_review_required=any(
                finding.human_review_required for finding in findings
            ),
        )

    def _finding(
        self,
        ctx: ComplianceContext,
        rule: ComplianceRule,
        *,
        status: ComplianceStatus,
        explanation: str,
        missing_information: list[str] | None = None,
        severity: Severity | None = None,
        evidence_refs: list[UUID] | None = None,
    ) -> ComplianceOutput:
        return ComplianceOutput(
            case_id=ctx.case_id,
            rule_id=rule.rule_id,
            rule_set_version=self.config.rule_set_version,
            status=status,
            severity=severity,
            affected_requirement=rule.requirement,
            evidence_refs=evidence_refs or [],
            missing_information=missing_information or [],
            explanation=explanation,
        )

    def _retrieve_evidence(
        self, rule: ComplianceRule, ctx: ComplianceContext
    ) -> list[EvidenceItem]:
        if rule.evidence_query is None:
            return [self._system_evidence(ctx)]

        try:
            items = self.retriever.retrieve(
                query=rule.evidence_query,
                state_code=ctx.state_code,
                loan_date=ctx.loan_date,
                top_k=3,
            )
        except Exception:  # noqa: BLE001 - retrieval failure must fail closed
            logger.exception("Evidence retrieval failed for %s", rule.rule_id)
            return []

        filtered: list[EvidenceItem] = []
        for item in items:
            if item.state_code is not None and item.state_code.upper() != ctx.state_code.upper():
                continue
            filtered.append(item)
        return filtered

    @staticmethod
    def _system_evidence(ctx: ComplianceContext) -> EvidenceItem:
        metadata = ctx.source_metadata
        payload = {
            "source_last_success_at": metadata.get("source_last_success_at"),
            "source_effective_to": metadata.get("source_effective_to"),
            "index_version": metadata.get("index_version"),
            "active_index_version": metadata.get("active_index_version"),
        }
        return EvidenceItem(
            retrieval_ref="source_registry",
            source_name=str(metadata.get("source_name", "internal source registry")),
            authority=str(metadata.get("authority", "internal source registry")),
            version_or_date=str(
                metadata.get("source_version_or_date", "source registry metadata")
            ),
            section_or_page="source freshness and index coverage",
            scope="national",
            snippet=json.dumps(payload, sort_keys=True),
            score=1.0,
            index_version=str(metadata.get("index_version", "unknown")),
        )
