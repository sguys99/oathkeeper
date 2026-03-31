"""Per-deal analysis context — accumulates structured results across meta-tool calls."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


_registry: dict[str, AnalysisContext] = {}


@dataclass
class AnalysisContext:
    """Mutable accumulator for one deal's analysis results."""

    deal_id: str
    deal_input: str

    # Accumulated results (mirrors AgentState fields)
    structured_deal: dict = field(default_factory=dict)
    scores: list[dict] = field(default_factory=list)
    total_score: float = 0.0
    verdict: str = "pending"
    resource_estimate: dict = field(default_factory=dict)
    risks: list[dict] = field(default_factory=list)
    risk_interdependencies: list[dict] = field(default_factory=list)
    similar_projects: list[dict] = field(default_factory=list)
    final_report: str = ""
    errors: list[str] = field(default_factory=list)

    # Progress callback: async fn(step_label: str) -> None
    on_progress: Callable[[str], Awaitable[None]] | None = None

    def to_result_dict(self) -> dict:
        """Export accumulated results as a dict matching service.py expectations."""
        return {
            "structured_deal": self.structured_deal,
            "scores": self.scores,
            "total_score": self.total_score,
            "verdict": self.verdict,
            "resource_estimate": self.resource_estimate,
            "risks": self.risks,
            "risk_interdependencies": self.risk_interdependencies,
            "similar_projects": self.similar_projects,
            "final_report": self.final_report,
            "errors": self.errors,
        }

    def to_agent_state(self) -> dict:
        """Build a partial AgentState dict for passing to worker nodes."""
        return {
            "deal_id": self.deal_id,
            "deal_input": self.deal_input,
            **self.to_result_dict(),
        }


def init_analysis_context(
    deal_id: str,
    deal_input: str,
    on_progress: Callable[[str], Awaitable[None]] | None = None,
) -> AnalysisContext:
    """Create and register a new analysis context for the given deal."""
    ctx = AnalysisContext(deal_id=deal_id, deal_input=deal_input, on_progress=on_progress)
    _registry[deal_id] = ctx
    return ctx


def get_analysis_context(deal_id: str) -> AnalysisContext:
    """Retrieve the analysis context. Raises if not initialized."""
    if deal_id not in _registry:
        raise RuntimeError(f"AnalysisContext not initialized for deal {deal_id}")
    return _registry[deal_id]


def cleanup_analysis_context(deal_id: str) -> dict | None:
    """Remove and return the context as a result dict. Returns None if not found."""
    ctx = _registry.pop(deal_id, None)
    return ctx.to_result_dict() if ctx else None
