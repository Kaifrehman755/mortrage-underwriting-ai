"""Regulatory Compliance Agent.

Runs the deterministic India starter rule pack against a shared case state,
attaches ``EvidenceItem`` references, and emits an audit event. The agent never
uses an LLM to decide a status and never converts an unevidenced result into a
flag: the engine downgrades those to ``cannot_verify``.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from app.compliance.config import ComplianceConfig
from app.compliance.engine import ComplianceEngine, EvidenceRetriever
from app.compliance.rules.base import ComplianceContext
from app.compliance.schemas import ComplianceOutput, ComplianceRun, ComplianceStatus
from app.property.schemas import AuditEvent, SharedCaseState

logger = logging.getLogger(__name__)


def _digest(data: Any) -> str:
    payload = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ComplianceAgent:
    """Orchestrates rule evaluation and evidence attachment for one case."""

    def __init__(
        self,
        engine: ComplianceEngine | None = None,
        retriever: EvidenceRetriever | None = None,
        config: ComplianceConfig | None = None,
        model_version: str = "1.0.0",
    ):
        self.engine = engine or ComplianceEngine(
            retriever=retriever,
            config=config,
        )
        self.model_version = model_version

    def evaluate(self, state: SharedCaseState) -> SharedCaseState:
        """Run compliance checks and update the shared case state."""
        subject = state.subject_property
        loan_date = state.loan_data.get("loan_date")
        source_metadata = state.loan_data.get("source_metadata", {})
        if not isinstance(source_metadata, dict):
            source_metadata = {}

        input_digest = _digest(
            {
                "case_id": state.case_id,
                "subject": subject.model_dump(),
                "loan_data": state.loan_data,
                "source_metadata": source_metadata,
                "rule_set_version": self.engine.config.rule_set_version,
            }
        )

        context = ComplianceContext(
            case_id=state.case_id,
            state_code=subject.state_code,
            loan_date=str(loan_date) if loan_date is not None else None,
            loan_data=state.loan_data,
            valuation=state.model_output,
            market_facts=state.market_facts,
            notes=str(state.loan_data.get("notes", "")),
            features=state.loan_data.get("features", []),
            source_metadata=source_metadata,
        )

        try:
            run = self.engine.run(context)
        except Exception:  # noqa: BLE001 - last-resort agent boundary
            logger.exception("Compliance engine failed for case %s", state.case_id)
            run = self._failed_run(state.case_id)

        self._apply_run(state, run)

        output_digest = _digest(
            {
                "findings": [finding.model_dump(mode="json") for finding in run.findings],
                "evidence_ids": [item.evidence_id for item in run.evidence],
                "human_review_required": state.human_review_required,
                "status": state.status,
            }
        )
        state.audit_trail.append(
            AuditEvent(
                case_id=state.case_id,
                actor="compliance_agent",
                node="compliance_check",
                input_digest=input_digest,
                output_digest=output_digest,
                model_version=self.model_version,
                details={
                    **run.summary(),
                    "missing_information_count": len(run.missing_information),
                    "index_version": source_metadata.get("index_version"),
                },
            )
        )
        return state

    def _apply_run(self, state: SharedCaseState, run: ComplianceRun) -> None:
        state.evidence = [item.model_dump(mode="json") for item in run.evidence]
        state.compliance = [
            finding.model_dump(mode="json") for finding in run.findings
        ]

        merged_missing = list(state.missing_information)
        for item in run.missing_information:
            if item not in merged_missing:
                merged_missing.append(item)
        state.missing_information = merged_missing

        valuation_needs_review = bool(
            state.model_output
            and (
                state.model_output.abstain_reason is not None
                or state.model_output.human_review_required
            )
        )
        state.human_review_required = (
            state.human_review_required or run.human_review_required or valuation_needs_review
        )
        state.status = "needs_review" if state.human_review_required else "compliance_checked"

    def _failed_run(self, case_id: str) -> ComplianceRun:
        summary = "Cannot verify: the compliance engine failed. Human review required."
        findings = [
            ComplianceOutput(
                case_id=case_id,
                rule_id=rule.rule_id,
                rule_set_version=self.engine.config.rule_set_version,
                status=ComplianceStatus.CANNOT_VERIFY,
                affected_requirement=rule.requirement,
                missing_information=[
                    f"compliance engine result for {rule.rule_id}",
                ],
                explanation=summary,
            )
            for rule in self.engine.rules
        ]
        missing: list[str] = []
        for finding in findings:
            for item in finding.missing_information:
                if item not in missing:
                    missing.append(item)
        return ComplianceRun(
            case_id=case_id,
            rule_set_version=self.engine.config.rule_set_version,
            findings=findings,
            missing_information=missing,
            human_review_required=True,
        )
