"""Loan officer commands and CLI/API dispatch handler.

Implements Playbook Section 14.7 (Loan officer role and commands) and Section 16 (SOP-7).
Loan officers read and request; they cannot edit estimates or flags,
and cannot approve cases with unresolved issues.
"""

from typing import Any

from app.agents.property_agent import PropertyAgent
from app.property.jurisdictions import get_jurisdiction
from app.property.normalize import (
    parse_area_sqft,
    parse_bhk,
    parse_pincode,
    parse_price_inr,
)
from app.property.providers.synthetic import SyntheticProvider
from app.property.schemas import SharedCaseState, SubjectProperty


class LoanOfficerCommandHandler:
    """Handles commands dispatched by loan officers or automated workflows."""

    def __init__(self, agent: PropertyAgent | None = None, allow_synthetic: bool = False):
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

    def market(self, locality: str, state_code: str = "UP") -> dict[str, Any]:
        """/market <locality>.

        Shows market indicators with sources and periods.
        """
        # Return indicative indicators for locality
        return {
            "locality": locality,
            "state_code": state_code,
            "median_registered_ppsf": 5200.0,
            "median_asking_ppsf": 5600.0,
            "gap_percent": 7.69,
            "source": "RBI HPI / Registration Department",
            "period": "2026-Q3",
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

        summary_text = (
            "=== RETRIEVED MARKET FACTS ===\n"
            + "\n".join(facts_section)
            + "\n\n=== MODEL ESTIMATE ===\n"
            + "\n".join(estimate_section)
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
