
"""Decision and Underwriting Recommendation Agent.

Combines assessment findings and routes cases for a final decision
or human review. Final lending criteria must come from an approved policy.
"""

from typing import Any


class DecisionAgent:
    """Agent for synthesizing underwriting assessment results."""

    VALID_POLICY_OUTCOMES = {"pass", "fail", "review"}

    def evaluate(self, assessment: dict[str, Any]) -> dict[str, Any]:
        """Evaluate an assessment and return a structured recommendation."""

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
            field for field in required_fields
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

        if policy_outcome not in self.VALID_POLICY_OUTCOMES:
            raise ValueError(
                "policy_outcome must be 'pass', 'fail', or 'review'."
            )

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

        confidence = assessment["confidence"]

        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or not 0 <= confidence <= 1
        ):
            raise ValueError("confidence must be a number between 0 and 1.")

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
