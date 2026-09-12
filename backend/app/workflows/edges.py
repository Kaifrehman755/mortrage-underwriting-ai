"""Conditional edge routing for LangGraph underwriting workflows (Reserved for Phase 1+)."""

from typing import Literal

from app.workflows.state import UnderwritingState


def should_route_to_human_review(
    state: UnderwritingState,
) -> Literal["human_review", "finalize_decision"]:
    """Evaluate whether underwriting state requires manual underwriter intervention."""
    return "human_review" if state.get("human_review_required", False) else "finalize_decision"
