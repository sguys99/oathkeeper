"""Scoring node — evaluate structured deal against 7 criteria."""

import logging
import uuid

from backend.app.agent.base import (
    build_company_context,
    fetch_company_settings,
    format_company_context,
    format_scoring_criteria,
    logged_call_llm,
    parse_json_response,
    update_log_parsed_output,
)
from backend.app.agent.prompt_loader import load_prompt
from backend.app.agent.state import AgentState
from backend.app.db.repositories import settings_repo
from backend.app.db.session import AsyncSessionLocal
from backend.app.db.vector_store import CompanyContextStore

logger = logging.getLogger(__name__)


def _determine_verdict(total_score: float) -> str:
    """Server-side verdict based on score thresholds (don't trust LLM arithmetic)."""
    if total_score >= 70:
        return "go"
    if total_score >= 40:
        return "conditional_go"
    return "no_go"


def _recalculate_scores(scores: list[dict]) -> tuple[list[dict], float]:
    """Recompute weighted_score and total from LLM-provided raw scores."""
    recalculated = []
    total = 0.0
    for s in scores:
        score = float(s.get("score", 0))
        weight = float(s.get("weight", 0))
        weighted = round(score * weight, 2)
        total += weighted
        recalculated.append({**s, "score": score, "weight": weight, "weighted_score": weighted})
    return recalculated, round(total, 2)


def make_scoring_node(context_store: CompanyContextStore):
    """Factory — returns an async scoring node with injected dependencies."""

    async def scoring_node(state: AgentState) -> dict:
        try:
            structured_deal = state.get("structured_deal", {})

            # Fetch scoring criteria from DB (own session for concurrency safety)
            async with AsyncSessionLocal() as db:
                criteria = await settings_repo.list_active_criteria(db)
                company_settings = await fetch_company_settings(db)
            scoring_criteria = format_scoring_criteria(criteria)

            # Fetch company context
            query_text = structured_deal.get("project_summary", "")
            context_results = await context_store.query(query_text, top_k=5)
            vector_context = format_company_context(context_results)

            company_context = build_company_context(vector_context, company_settings)

            # Render prompts
            system_tpl = load_prompt("system")
            system_base = system_tpl.render_system(
                company_context=company_context,
                deal_criteria=company_settings.get("deal_criteria", ""),
            )

            tpl = load_prompt("scoring")
            system_prompt, user_prompt = tpl.render(
                system_base=system_base,
                structured_deal=structured_deal,
                scoring_criteria=scoring_criteria,
                company_context=company_context,
            )

            deal_id = uuid.UUID(state["deal_id"])
            raw, log_id = await logged_call_llm(
                system_prompt,
                user_prompt,
                deal_id=deal_id,
                node_name="scoring",
            )
            parsed = parse_json_response(raw)

            # Server-side recalculation for accuracy
            scores, total_score = _recalculate_scores(parsed.get("scores", []))
            verdict = _determine_verdict(total_score)

            await update_log_parsed_output(
                log_id,
                {
                    "scores": scores,
                    "total_score": total_score,
                    "verdict": verdict,
                },
            )

            return {
                "scores": scores,
                "total_score": total_score,
                "verdict": verdict,
            }

        except Exception:
            logger.exception("scoring node failed")
            return {
                "scores": [],
                "total_score": 0.0,
                "verdict": "pending",
                "errors": ["scoring: node execution failed"],
            }

    return scoring_node
