
"""Decision and Underwriting Recommendation Agent.

Combines assessment findings and routes cases for a final decision
or human review. Final lending criteria must come from an approved policy.
"""

import math
from typing import Any


class DecisionAgent:
    """Agent for synthesizing underwriting assessment results."""

    VALID_POLICY_OUTCOMES = {"pass", "fail", "review"}

    def evaluate(self, assessment: dict[str, Any]) -> dict[str, Any]:
        """Validate an assessment and return a structured recommendation."""

        required_fields = [
            "dti_percentage",
            "ltv",
            "cltv",
            "dscr",
            "fico_score",
            "risk_score",
            "documents_complete",
            "compliance_clear",
            "data_conflicts",
            "confidence",
            "policy_outcome",
        ]

        missing_fields = [
            field
            for field in required_fields
            if field not in assessment or assessment[field] is None
        ]

        if missing_fields:
            return {
                "agent": "decision",
                "recommendation": "SUSPEND",
                "requires_human_review": True,
                "reasons": [
                    f"Missing required assessment data: {', '.join(missing_fields)}"
                ],
            }

        policy_outcome = assessment["policy_outcome"]

        if (
            not isinstance(policy_outcome, str)
            or policy_outcome not in self.VALID_POLICY_OUTCOMES
        ):
            raise ValueError(
                "policy_outcome must be 'pass', 'fail', or 'review'."
            )

        # Validate financial metrics before making a decision.
        invalid_reasons: list[str] = []

        numeric_fields = [
            "dti_percentage",
            "ltv",
            "cltv",
            "dscr",
            "risk_score",
        ]

        for field in numeric_fields:
            value = assessment[field]

            if isinstance(value, bool) or not isinstance(value, (int, float)):
                invalid_reasons.append(f"{field} must be numeric.")
                continue

            try:
                is_finite = math.isfinite(value)
            except OverflowError:
                is_finite = False

            if not is_finite or value < 0:
                invalid_reasons.append(
                    f"{field} must be finite and non-negative."
                )

        risk_score = assessment["risk_score"]

        if (
            isinstance(risk_score, (int, float))
            and not isinstance(risk_score, bool)
            and risk_score > 100
        ):
            invalid_reasons.append("risk_score must not exceed 100.")

        fico = assessment["fico_score"]

        if isinstance(fico, bool) or not isinstance(fico, int):
            invalid_reasons.append("fico_score must be an integer.")
        elif not 300 <= fico <= 850:
            invalid_reasons.append(
                "fico_score must be between 300 and 850."
            )

        if invalid_reasons:
            return {
                "agent": "decision",
                "recommendation": "SUSPEND",
                "requires_human_review": True,
                "reasons": invalid_reasons,
            }

        # Validate confidence separately.
        confidence = assessment["confidence"]

        try:
            confidence_is_finite = (
                not isinstance(confidence, bool)
                and isinstance(confidence, (int, float))
                and math.isfinite(confidence)
            )
        except OverflowError:
            confidence_is_finite = False

        if (
            not confidence_is_finite
            or not 0 <= confidence <= 1
        ):
            raise ValueError(
                "confidence must be a number between 0 and 1."
            )

        # Identify conditions requiring human review.
        review_reasons: list[str] = []

        if assessment["documents_complete"] is not True:
            review_reasons.append("Required documents are incomplete.")

        if assessment["compliance_clear"] is not True:
            review_reasons.append(
                "Compliance clearance is missing or unresolved."
            )

        if assessment["data_conflicts"] is not False:
            review_reasons.append(
                "Assessment data contains conflicts or unresolved inconsistencies."
            )

        if confidence < 0.80:
            review_reasons.append(
                "Assessment confidence is below the illustrative 0.80 threshold."
            )

        if review_reasons or policy_outcome == "review":
            if policy_outcome == "review":
                review_reasons.append(
                    "The applicable underwriting policy requires further review."
                )

            return {
                "agent": "decision",
                "recommendation": "SUSPEND",
                "requires_human_review": True,
                "reasons": review_reasons,
            }

        if policy_outcome == "pass":
            return {
                "agent": "decision",
                "recommendation": "APPROVE",
                "requires_human_review": False,
                "reasons": [
                    "The supplied policy outcome passed and no review flags were found."
                ],
            }

        return {
            "agent": "decision",
            "recommendation": "DENY",
            "requires_human_review": False,
            "reasons": [
                "The supplied underwriting policy outcome was fail."
            ],
        }
