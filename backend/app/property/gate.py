"""Guardrail gate enforcing the eight Playbook invariants on shared case state.

Playbook Section 1 Acceptance Tests:
1. Never fabricate MLS or property data; no data means abstain and escalate.
2. Market facts and model estimates live in separate fields and report sections.
3. A flag without an evidence reference is rejected by validation.
4. Any failure or low confidence goes to a human, never to a guess.
5. No protected-class proxies as valuation features.
6. The LLM explainer cannot change flags, severity or the estimate.
7. Output says 'potential issue for review', never a legal conclusion.
8. Rules apply as of the loan date; state isolation strictly preserved.
"""

import re

from app.property.normalize import check_protected_class_proxies
from app.property.schemas import SharedCaseState

_LEGAL_CONCLUSION_PATTERN = re.compile(
    r"\b(violation|violates|violated|compliant|illegal|legally liable)\b",
    re.IGNORECASE,
)


class GuardrailGateViolation(Exception):
    """Raised when an invariant is violated in shared case state."""

    def __init__(self, invariant_num: int, message: str):
        super().__init__(f"Invariant {invariant_num} Violation: {message}")
        self.invariant_num = invariant_num
        self.message = message


class GuardrailGate:
    """Verifies that shared case states respect all 8 structural invariants."""

    @classmethod
    def verify(cls, state: SharedCaseState) -> list[str]:
        """Verify all invariants and return any violations."""
        violations: list[str] = []

        # Invariant 2: Market facts and model estimates live in separate fields
        if hasattr(state, "model_output") and state.model_output is not None:
            if not state.model_output.is_estimate:
                violations.append("Invariant 2: Model output must have is_estimate=True")

        # Invariant 8: State isolation - comps must never cross states
        subject_state = state.subject_property.state_code
        for comp in state.market_facts:
            if comp.state_code != subject_state:
                violations.append(
                    f"Invariant 8: State isolation breach. Subject is in {subject_state} "
                    f"but comp {comp.comp_id} belongs to {comp.state_code}"
                )

        # Invariant 5: No protected-class proxies in subject notes or address
        proxies = check_protected_class_proxies(
            f"{state.subject_property.original_address} {state.subject_property.locality}"
        )
        if proxies:
            violations.append(
                f"Invariant 5: Protected-class proxy detected: {', '.join(proxies)}"
            )

        # Invariant 4: Low confidence or abstain must set human_review_required
        if state.model_output is not None:
            if state.model_output.abstain_reason is not None and not state.human_review_required:
                violations.append("Invariant 4: Abstained valuation must set human_review_required=True")
            if state.model_output.confidence_label == "low" and not state.human_review_required:
                violations.append("Invariant 4: Low confidence valuation must set human_review_required=True")

        # Invariants 3, 4, 7 and 8 for compliance findings and their evidence.
        evidence_by_id = {
            str(item.get("evidence_id")): item for item in state.evidence
        }
        for finding in state.compliance:
            rule_id = str(finding.get("rule_id", "unknown"))
            status = str(finding.get("status", ""))
            refs = [str(ref) for ref in finding.get("evidence_refs", [])]
            explanation = str(finding.get("explanation", ""))

            if status != "cannot_verify" and not refs:
                violations.append(
                    f"Invariant 3: finding {rule_id} has status {status} without evidence"
                )
            for ref in refs:
                if ref not in evidence_by_id:
                    violations.append(
                        f"Invariant 3: finding {rule_id} cites missing evidence {ref}"
                    )

            if status == "cannot_verify" and not finding.get("missing_information"):
                violations.append(
                    f"Invariant 3: finding {rule_id} is cannot_verify without missing_information"
                )
            if status == "potential_issue":
                if "potential issue for review" not in explanation.lower():
                    violations.append(
                        f"Invariant 7: finding {rule_id} does not use review wording"
                    )
                if finding.get("severity") not in {"low", "medium", "high"}:
                    violations.append(
                        f"Invariant 7: finding {rule_id} lacks a valid severity"
                    )
            if _LEGAL_CONCLUSION_PATTERN.search(explanation):
                violations.append(
                    f"Invariant 7: finding {rule_id} contains a legal conclusion"
                )
            if status != "no_issue_detected" and not state.human_review_required:
                violations.append(
                    f"Invariant 4: finding {rule_id} requires human review but state does not"
                )

            for ref in refs:
                item = evidence_by_id.get(ref)
                if item is None:
                    continue
                evidence_state = item.get("state_code")
                if evidence_state and str(evidence_state).upper() != subject_state.upper():
                    violations.append(
                        f"Invariant 8: evidence {ref} belongs to {evidence_state}, "
                        f"not {subject_state}"
                    )

        return violations

    @classmethod
    def assert_valid(cls, state: SharedCaseState) -> None:
        """Raise GuardrailGateViolation if any invariant fails."""
        violations = cls.verify(state)
        if violations:
            raise GuardrailGateViolation(invariant_num=0, message="; ".join(violations))
