from typing import Any

from app.calculations.credit_analysis import calculate_credit_analysis


class CreditAgent:
    """Agent for evaluating a borrower's credit score."""

    def analyze(self, fico_score: int) -> dict[str, Any]:
        """Analyze a FICO score using the existing calculation module."""

        credit_result = calculate_credit_analysis(fico_score)

        return {
            "agent": "credit_analysis",
            "status": "completed",
            "credit_analysis": credit_result,
        }
