"""Loan officer commands and CLI/API dispatch handler.

Implements Playbook Section 14.7 (Loan officer role and commands) and Section 16 (SOP-7).
Loan officers read and request; they cannot edit estimates or flags,
and cannot approve cases with unresolved issues.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from app.agents.compliance_agent import ComplianceAgent
from app.agents.property_agent import PropertyAgent
from app.compliance.schemas import ComplianceStatus, Severity
from app.property.jurisdictions import get_jurisdiction
from app.property.normalize import (
    parse_area_sqft,
    parse_bhk,
    parse_pincode,
    parse_price_inr,
)
from app.property.providers.synthetic import SyntheticProvider
from app.property.schemas import AuditEvent, SharedCaseState, SubjectProperty

_ALLOWED_OPERATIONAL_ROLES = {"loan_officer", "compliance_reviewer", "admin"}
_REVIEW_ROLES = {"compliance_reviewer", "admin"}


def _digest(data: Any) -> str:
    payload = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class LoanOfficerCommandHandler:
    """Handles commands dispatched by loan officers or automated workflows."""

    def __init__(
        self,
        agent: PropertyAgent | None = None,
        allow_synthetic: bool = False,
        compliance_agent: ComplianceAgent | None = None,
    ):
        # F-01: no silent synthetic default. Production callers must inject an
        # agent backed by an approved provider; allow_synthetic is test-only.
        if agent is None:
            if not allow_synthetic:
                raise ValueError(
                    "LoanOfficerCommandHandler requires an injected PropertyAgent "
                    "backed by an approved provider."
                )
            agent = PropertyAgent(provider=SyntheticProvider(), allow_synthetic=True)
        self.agent = agent
        # The default compliance agent has a null retriever, so every
        # evidence-dependent rule fails closed instead of using synthetic text.
        self.compliance_agent = compliance_agent or ComplianceAgent()
        self.cases: dict[str, SharedCaseState] = {}

    def intake(
        self,
        case_id: str,
        address: str,
        locality: str,
        city: str,
        state_code: str,
        living_area_raw: str | float,
        price_quoted_raw: str | float | None = None,
        property_type: str = "apartment",
        area_basis: str = "carpet",
        lat: float = 26.8530,
        lon: float = 80.9980,
    ) -> dict[str, Any]:
        """/intake <address> --type --area --basis --price-quoted.

        Creates the case and normalizes the subject property.
        """
        sqft = parse_area_sqft(living_area_raw)
        if not sqft:
            raise ValueError(f"Invalid living area '{living_area_raw}'. Must be greater than 0.")

        price = parse_price_inr(price_quoted_raw) if price_quoted_raw else None
        bhk = parse_bhk(address)
        pin = parse_pincode(address)

        # Validate jurisdiction exists
        get_jurisdiction(state_code)

        subject = SubjectProperty(
            original_address=address,
            address_norm=address.strip(),
            locality=locality,
            city=city,
            state_code=state_code.upper(),
            pincode=pin,
            property_type=property_type,
            beds=float(bhk) if bhk else None,
            living_area_sqft=sqft,
            area_basis=area_basis,  # type: ignore
            lat=lat,
            lon=lon,
            quoted_price=price,
        )

        state = SharedCaseState(
            case_id=case_id,
            subject_property=subject,
            status="intake_done",
        )
        self.cases[case_id] = state

        return {
            "case_id": case_id,
            "status": "intake_done",
            "subject": subject.model_dump(),
            "message": f"Case {case_id} intake complete for {subject.address_norm}.",
        }

    def valuate(self, case_id: str) -> dict[str, Any]:
        """/valuate <case_id>.

        Runs comps and returns estimate with interval, or an abstain reason.
        """
        if case_id not in self.cases:
            raise KeyError(f"Case '{case_id}' not found.")

        state = self.cases[case_id]
        updated_state = self.agent.evaluate(state)
        self.cases[case_id] = updated_state

        vo = updated_state.model_output
        return {
            "case_id": case_id,
            "status": updated_state.status,
            "estimate": vo.estimate if vo else None,
            "interval_low": vo.interval_low if vo else None,
            "interval_high": vo.interval_high if vo else None,
            "confidence_label": vo.confidence_label if vo else "low",
            "abstain_reason": vo.abstain_reason if vo else None,
            "human_review_required": updated_state.human_review_required,
            "n_comps": vo.n_comps if vo else 0,
            "is_estimate": True,
        }

    def comps(self, case_id: str, radius_km: float = 3.0, months: int = 12) -> dict[str, Any]:
        """/comps <case_id> --radius --months.

        Lists comparable sales with price type, area basis, distance, price per sq ft.
        """
        if case_id not in self.cases:
            raise KeyError(f"Case '{case_id}' not found.")

        state = self.cases[case_id]
        return {
            "case_id": case_id,
            "count": len(state.market_facts),
            "comps": [
                {
                    "comp_id": c.comp_id,
                    "address": c.address,
                    "locality": c.locality,
                    "sale_price": c.sale_price,
                    "living_area_sqft": c.living_area_sqft,
                    "price_per_sqft": c.price_per_sqft,
                    "price_type": c.price_type,
                    "area_basis": c.area_basis,
                    "distance_km": c.distance_km,
                    "sale_date": c.sale_date,
                    "is_synthetic": c.is_synthetic,
                }
                for c in state.market_facts
            ],
        }

    def market(
        self,
        locality: str,
        state_code: str = "UP",
        case_id: str | None = None,
    ) -> dict[str, Any]:
        """/market <locality> --case.

        Shows only indicators that were actually retrieved for a case. Without a
        case, the command abstains rather than returning fabricated locality
        statistics.
        """
        if case_id is not None:
            state = self._case(case_id)
            indicators = state.market_indicators
            if indicators:
                return {
                    "locality": locality,
                    "state_code": state_code,
                    "status": "available",
                    "indicators": indicators,
                    "source": "case_market_indicators",
                    "human_review_required": state.human_review_required,
                }

        return {
            "locality": locality,
            "state_code": state_code,
            "status": "cannot_verify",
            "reason": "market_indicator_source_unavailable",
            "indicators": {},
            "human_review_required": True,
            "message": (
                "No sourced market indicator is attached to a case. "
                "Market data was not fabricated."
            ),
        }

    def explain(self, case_id: str) -> dict[str, Any]:
        """/explain <case_id>.

        Generates structured plain-language summary strictly adhering to Invariant 6:
        - Cannot change flags, severity, or the estimate.
        - Uses 'potential issue for review', 'estimate', never a legal conclusion.
        - Separates market facts and model estimates.
        """
        if case_id not in self.cases:
            raise KeyError(f"Case '{case_id}' not found.")

        state = self.cases[case_id]
        vo = state.model_output
        subj = state.subject_property

        facts_section = [
            f"Subject: {subj.address_norm}, {subj.locality}, {subj.city} ({subj.state_code})",
            f"Living Area: {subj.living_area_sqft} sq ft ({subj.area_basis})",
            f"Comps Analyzed: {len(state.market_facts)} market transactions",
        ]

        if vo and vo.estimate is not None:
            estimate_section = [
                f"Model Estimate: INR {vo.estimate:,.2f} (is_estimate=True)",
                f"80% Confidence Interval: INR {vo.interval_low:,.2f} - INR {vo.interval_high:,.2f}" if vo.interval_low else "Interval: Not enough comps for bootstrap interval",
                f"Confidence Level: {vo.confidence_label.upper()} ({vo.confidence_level})",
                f"Dispersion: CV {vo.dispersion}",
            ]
        else:
            reason = vo.abstain_reason if vo else "valuation_not_executed"
            estimate_section = [
                "Model Estimate: Abstained (No estimate calculated)",
                f"Reason: potential issue for review - {reason}",
                "Status: human review required",
            ]

        compliance_section: list[str] = []
        if state.compliance:
            compliance_section = ["", "", "=== COMPLIANCE FINDINGS ==="]
            for finding in state.compliance:
                compliance_section.append(
                    f"{finding.get('rule_id')}: {finding.get('status')} - "
                    f"{finding.get('explanation')} "
                    f"(evidence refs: {len(finding.get('evidence_refs', []))})"
                )

        summary_text = (
            "=== RETRIEVED MARKET FACTS ===\n"
            + "\n".join(facts_section)
            + "\n\n=== MODEL ESTIMATE ===\n"
            + "\n".join(estimate_section)
            + "\n".join(compliance_section)
        )

        return {
            "case_id": case_id,
            "plain_language_summary": summary_text,
            "human_review_required": state.human_review_required,
        }

    def escalate(self, case_id: str, reason: str) -> dict[str, Any]:
        """/escalate <case_id> --reason.

        Sends the case to human reviewer with documented rationale.
        """
        if case_id not in self.cases:
            raise KeyError(f"Case '{case_id}' not found.")

        state = self.cases[case_id]
        state.human_review_required = True
        state.status = "needs_review"

        return {
            "case_id": case_id,
            "status": "needs_review",
            "escalated": True,
            "reason": reason,
            "message": f"Case {case_id} successfully escalated to compliance reviewer.",
        }

    def compliance(self, case_id: str) -> dict[str, Any]:
        """/compliance <case_id>.

        Runs deterministic compliance rules and attaches evidence references.
        """
        state = self._case(case_id)
        updated = self.compliance_agent.evaluate(state)
        self.cases[case_id] = updated
        counts = {status.value: 0 for status in ComplianceStatus}
        for finding in updated.compliance:
            counts[str(finding.get("status"))] = counts.get(str(finding.get("status")), 0) + 1
        return {
            "case_id": case_id,
            "status": updated.status,
            "finding_count": len(updated.compliance),
            "status_counts": counts,
            "human_review_required": updated.human_review_required,
            "missing_information": updated.missing_information,
            "findings": updated.compliance,
        }

    def evidence(self, case_id: str, finding_id: str) -> dict[str, Any]:
        """/evidence <case_id> <finding_id>.

        Returns the finding and only the evidence cited by that finding.
        """
        state = self._case(case_id)
        finding = next(
            (
                item
                for item in state.compliance
                if str(item.get("finding_id")) == str(finding_id)
            ),
            None,
        )
        if finding is None:
            raise KeyError(f"Finding '{finding_id}' not found in case '{case_id}'.")
        refs = {str(ref) for ref in finding.get("evidence_refs", [])}
        evidence = [item for item in state.evidence if str(item.get("evidence_id")) in refs]
        return {
            "case_id": case_id,
            "finding": finding,
            "evidence": evidence,
            "evidence_count": len(evidence),
        }

    def missing(self, case_id: str) -> dict[str, Any]:
        """/missing <case_id>. Lists unresolved information without guessing."""
        state = self._case(case_id)
        return {
            "case_id": case_id,
            "missing_information": state.missing_information,
            "count": len(state.missing_information),
            "human_review_required": state.human_review_required,
        }

    def review(
        self,
        case_id: str,
        decision: str,
        note: str = "",
        reviewer: str = "unknown",
        role: str = "compliance_reviewer",
    ) -> dict[str, Any]:
        """/review <case_id> --decision --note. Human-review gate only."""
        self._require_role(role, _REVIEW_ROLES)
        state = self._case(case_id)
        if decision not in {"accept", "reject", "request_more_info"}:
            raise ValueError(
                "decision must be one of: accept, reject, request_more_info"
            )

        open_findings = [
            finding
            for finding in state.compliance
            if finding.get("status") != ComplianceStatus.NO_ISSUE_DETECTED.value
        ]
        if decision in {"accept", "reject"} and open_findings and not note.strip():
            raise ValueError("A reviewer note is required when open findings remain.")

        if decision == "request_more_info":
            state.status = "needs_review"
            state.human_review_required = True
        elif decision == "accept":
            state.status = "reviewed"
            state.human_review_required = False
        else:
            state.status = "rejected"
            state.human_review_required = False

        self._append_audit(
            state,
            actor=reviewer,
            node="human_review",
            details={"decision": decision, "note": note, "role": role},
        )
        return {
            "case_id": case_id,
            "status": state.status,
            "decision": decision,
            "reviewer": reviewer,
            "human_review_required": state.human_review_required,
        }

    def approve(self, case_id: str, role: str = "compliance_reviewer") -> dict[str, Any]:
        """/approve <case_id>. Blocked by unresolved high-severity findings."""
        self._require_role(role, _REVIEW_ROLES)
        state = self._case(case_id)
        if not state.compliance:
            raise ValueError("Run /compliance before /approve.")

        blocking = [
            finding
            for finding in state.compliance
            if finding.get("status") == ComplianceStatus.CANNOT_VERIFY.value
            or (
                finding.get("status") == ComplianceStatus.POTENTIAL_ISSUE.value
                and finding.get("severity") == Severity.HIGH.value
            )
        ]
        if blocking:
            raise ValueError(
                "Cannot approve: unresolved high-severity or cannot_verify findings "
                f"remain ({len(blocking)})."
            )

        state.status = "approved"
        state.human_review_required = False
        self._append_audit(
            state,
            actor=role,
            node="approval",
            details={"findings": len(state.compliance)},
        )
        return {
            "case_id": case_id,
            "status": "approved",
            "human_review_required": False,
            "eligible": True,
        }

    def sources(self, role: str = "admin") -> dict[str, Any]:
        """/sources. Admin-only view of source approval state."""
        self._require_role(role, {"admin"})
        path = Path(__file__).resolve().parents[1] / "rag" / "sources.yaml"
        if not path.exists():
            return {"documents": [], "count": 0, "approved_count": 0}
        with path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        documents = payload.get("documents", [])
        if not isinstance(documents, list):
            documents = []
        approved_count = sum(1 for doc in documents if doc.get("approved") is True)
        return {
            "documents": documents,
            "count": len(documents),
            "approved_count": approved_count,
            "warning": (
                "Documents without approved=true are excluded from production retrieval."
            ),
        }

    def _case(self, case_id: str) -> SharedCaseState:
        if case_id not in self.cases:
            raise KeyError(f"Case '{case_id}' not found.")
        return self.cases[case_id]

    @staticmethod
    def _require_role(role: str, allowed: set[str]) -> None:
        if role not in allowed:
            raise PermissionError(
                f"Role '{role}' is not permitted; allowed roles: {sorted(allowed)}"
            )

    @staticmethod
    def _append_audit(
        state: SharedCaseState,
        *,
        actor: str,
        node: str,
        details: dict[str, Any],
    ) -> None:
        state.audit_trail.append(
            AuditEvent(
                case_id=state.case_id,
                actor=actor,
                node=node,
                input_digest=_digest(details),
                output_digest=_digest(
                    {"status": state.status, "human_review_required": state.human_review_required}
                ),
                details=details,
            )
        )
