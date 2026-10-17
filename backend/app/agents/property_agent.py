"""Property Valuation Agent.

Adheres to Playbook Section 1, 5, 7, 14, 18:
- Orchestrates property intake, comps retrieval, valuation, and confidence scoring.
- Invariant 1: Never fabricates data; handles provider failure with escalation.
- Invariant 2: Separates market_facts from model_output in shared state.
- Invariant 4: Low confidence or abstain sets human_review_required.
- Invariant 6: LLM explainer cannot change flags, severity or estimate.
- Emits cryptographic sha256 audit events on every run.
"""

import hashlib
import json
import logging
from typing import Any

from app.property.jurisdictions import get_jurisdiction
from app.property.provider import CompProvider, ProviderUnavailable
from app.property.providers.synthetic import SyntheticProvider
from app.property.schemas import (
    AuditEvent,
    ComparableRecord,
    SharedCaseState,
    ValuationOutput,
)
from app.property.valuation import PropertyValuationEngine

logger = logging.getLogger(__name__)


# F-14: generic, non-sensitive reason codes. Raw exception text must never be
# embedded in outputs, shared state or audit details shown to a client.
UNEXPECTED_AGENT_ERROR = "unexpected_agent_error"


def compute_sha256_digest(data: Any) -> str:
    """Compute sha256 hexadecimal hash for audit reproducibility."""
    payload_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()


def _correlation_id(case_id: str, input_digest: str) -> str:
    """Derive a short, non-sensitive correlation id linking a log line to its case."""
    return compute_sha256_digest({"case_id": case_id, "input_digest": input_digest})[:12]


class PropertyAgent:
    """Agent orchestrator for property appraisal, comps analysis, and collateral valuation."""

    def __init__(
        self,
        provider: CompProvider | None = None,
        engine: PropertyValuationEngine | None = None,
        model_version: str = "1.0.0",
        allow_synthetic: bool = False,
    ):
        # F-01: never silently default to synthetic market data. A production
        # agent must receive an explicitly injected, approved provider.
        if provider is None:
            raise ValueError(
                "PropertyAgent requires an explicitly injected CompProvider; "
                "refusing to default to synthetic comparables."
            )
        # F-01: synthetic providers are a test-only mechanism and must be opted
        # into explicitly, so synthetic rows cannot reach a production estimate.
        if isinstance(provider, SyntheticProvider) and not allow_synthetic:
            raise ValueError(
                "SyntheticProvider is test-only. Pass allow_synthetic=True "
                "explicitly to opt in to synthetic fixtures."
            )
        self.provider = provider
        self.allow_synthetic = allow_synthetic
        self.engine = engine or PropertyValuationEngine(
            model_version=model_version, allow_synthetic=allow_synthetic
        )
        self.model_version = model_version

    def evaluate(self, state: SharedCaseState) -> SharedCaseState:
        """Execute end-to-end property appraisal and update shared case state."""
        case_id = state.case_id
        subject = state.subject_property

        # Compute input digest
        input_digest = compute_sha256_digest({
            "case_id": case_id,
            "subject": subject.model_dump(),
            "loan_data": state.loan_data,
        })

        try:
            # 1. Verify jurisdiction
            jurisdiction = get_jurisdiction(subject.state_code)
            if jurisdiction.status not in ("pilot", "live"):
                valuation = ValuationOutput(
                    case_id=case_id,
                    subject_id=subject.property_id,
                    abstain_reason=f"state_{subject.state_code}_not_live_status_{jurisdiction.status}",
                    confidence_label="low",
                    confidence_level=0.0,
                    model_version=self.model_version,
                )
                return self._finalize_state(
                    state=state,
                    valuation=valuation,
                    market_facts=[],
                    input_digest=input_digest,
                    note="State not supported or not live.",
                )

            # 2. Fetch comps from authorized provider
            raw_comps = self.provider.fetch_comps(
                subject=subject,
                radius_km=5.0,
                months=18,
                filters={"property_type": subject.property_type},
            )

            # 3. Run valuation engine
            valuation = self.engine.valuate(
                case_id=case_id,
                subject=subject,
                available_comps=raw_comps,
            )

            # Extract selected comps
            selected_comp_ids = set(valuation.comp_ids)
            selected_comps = [c for c in raw_comps if c.comp_id in selected_comp_ids]

            return self._finalize_state(
                state=state,
                valuation=valuation,
                market_facts=selected_comps,
                input_digest=input_digest,
                note="Valuation completed successfully.",
            )

        except ProviderUnavailable as e:
            logger.error(f"Provider unavailable for case {case_id}: {e}")
            valuation = ValuationOutput(
                case_id=case_id,
                subject_id=subject.property_id,
                abstain_reason="provider_unavailable",
                confidence_label="low",
                confidence_level=0.0,
                model_version=self.model_version,
            )
            return self._finalize_state(
                state=state,
                valuation=valuation,
                market_facts=[],
                input_digest=input_digest,
                note=f"Provider unavailable: {e.message}",
            )
        except Exception:  # noqa: BLE001 - last-resort orchestration boundary
            # F-14: the full traceback is logged server-side against a correlation id;
            # only a generic reason code and the correlation id reach the output/state,
            # so raw exception text cannot leak to a client or into a stored estimate.
            correlation_id = _correlation_id(case_id, input_digest)
            logger.exception(
                "Unexpected error in PropertyAgent (correlation_id=%s, case_id=%s)",
                correlation_id,
                case_id,
            )
            valuation = ValuationOutput(
                case_id=case_id,
                subject_id=subject.property_id,
                abstain_reason=UNEXPECTED_AGENT_ERROR,
                confidence_label="low",
                confidence_level=0.0,
                model_version=self.model_version,
            )
            return self._finalize_state(
                state=state,
                valuation=valuation,
                market_facts=[],
                input_digest=input_digest,
                note=f"Agent internal error (correlation_id={correlation_id}).",
                correlation_id=correlation_id,
            )

    def _finalize_state(
        self,
        state: SharedCaseState,
        valuation: ValuationOutput,
        market_facts: list[ComparableRecord],
        input_digest: str,
        note: str,
        correlation_id: str | None = None,
    ) -> SharedCaseState:
        """Update shared state, enforce invariants, and emit immutable audit event."""
        # Invariant 2: market facts and model output live in separate fields
        state.market_facts = market_facts
        state.model_output = valuation
        state.market_indicators = valuation.market_indicators

        # Invariant 4: low confidence or abstain sets human_review_required
        if valuation.human_review_required or valuation.abstain_reason is not None:
            state.human_review_required = True
            state.status = "needs_review"
        else:
            state.status = "valued"

        # Compute output digest
        output_digest = compute_sha256_digest({
            "valuation": valuation.model_dump(),
            "market_facts_count": len(market_facts),
            "human_review_required": state.human_review_required,
        })

        # Emit audit event
        audit_event = AuditEvent(
            case_id=state.case_id,
            actor="property_agent",
            node="property_valuation",
            input_digest=input_digest,
            output_digest=output_digest,
            model_version=self.model_version,
            details={
                "note": note,
                "n_comps": valuation.n_comps,
                "dispersion": valuation.dispersion,
                "abstain_reason": valuation.abstain_reason,
                # F-14: safe, non-sensitive id for cross-referencing server logs.
                "correlation_id": correlation_id,
            },
        )
        state.audit_trail.append(audit_event)

        return state
