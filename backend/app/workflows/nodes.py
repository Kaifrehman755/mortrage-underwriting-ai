"""LangGraph node execution functions (Reserved for Phase 1+)."""

from typing import Any

from app.workflows.state import UnderwritingState


async def document_ingestion_node(state: UnderwritingState) -> dict[str, Any]:
    """Placeholder node for ingesting and classifying documents."""
    return {}


async def financial_calculation_node(state: UnderwritingState) -> dict[str, Any]:
    """Placeholder node for running deterministic financial computations."""
    return {}


async def compliance_check_node(state: UnderwritingState) -> dict[str, Any]:
    """Placeholder node for regulatory guideline checking."""
    return {}


async def decision_synthesis_node(state: UnderwritingState) -> dict[str, Any]:
    """Placeholder node for assembling final recommendation."""
    return {}
