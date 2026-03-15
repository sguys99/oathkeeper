"""LangGraph agent state — shared TypedDict flowing through all graph nodes."""

import operator
from typing import Annotated, TypedDict


class AgentState(TypedDict, total=False):
    """State container for the deal-analysis LangGraph pipeline.

    ``total=False`` so that individual nodes can return partial dicts;
    LangGraph merges them into the accumulated state automatically.
    """

    # ── Input ──────────────────────────────────────────────────────────
    deal_id: str  # UUID as string (set once at graph invocation)
    deal_input: str  # raw deal text (set once at graph invocation)

    # ── Intermediate results ───────────────────────────────────────────
    structured_deal: dict  # output of deal_structuring node
    scores: list[dict]  # list of ScoreDetail-shaped dicts
    total_score: float  # weighted sum of scores
    verdict: str  # go | conditional_go | no_go | pending
    resource_estimate: dict  # ResourceEstimate-shaped dict
    risks: list[dict]  # list of RiskItem-shaped dicts
    similar_projects: list[dict]  # list of SimilarProject-shaped dicts

    # ── Final output ───────────────────────────────────────────────────
    final_report: str  # markdown report from final_verdict node

    # ── Pipeline metadata ──────────────────────────────────────────────
    status: str  # current pipeline phase
    errors: Annotated[list[str], operator.add]  # accumulated errors (parallel-safe)
