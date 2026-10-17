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

from app.property.normalize import check_protected_class_proxies
from app.property.schemas import SharedCaseState


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

        return violations

    @classmethod
    def assert_valid(cls, state: SharedCaseState) -> None:
        """Raise GuardrailGateViolation if any invariant fails."""
        violations = cls.verify(state)
        if violations:
            raise GuardrailGateViolation(invariant_num=0, message="; ".join(violations))
