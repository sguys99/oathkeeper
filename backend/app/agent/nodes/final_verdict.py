"""Final verdict node — generate executive markdown report."""

import logging
import uuid

from backend.app.agent.base import (
    build_company_context,
    fetch_company_settings,
    format_company_context,
    logged_call_llm,
)
from backend.app.agent.prompt_loader import load_prompt
from backend.app.agent.state import AgentState
from backend.app.db.session import AsyncSessionLocal
from backend.app.db.vector_store import CompanyContextStore

logger = logging.getLogger(__name__)


def make_final_verdict_node(context_store: CompanyContextStore):
    """Factory — returns an async final-verdict node."""

    async def final_verdict_node(state: AgentState) -> dict:
        try:
            structured_deal = state.get("structured_deal", {})

            # Build system base prompt with company context
            async with AsyncSessionLocal() as db:
                company_settings = await fetch_company_settings(db)

            overview = structured_deal.get("project_overview", {})
            if isinstance(overview, dict):
                query_text = " ".join(
                    filter(None, [overview.get("objective", ""), overview.get("scope", "")]),
                )
            else:
                query_text = str(overview) if overview else ""
            context_results = await context_store.query(query_text, top_k=5)
            vector_context = format_company_context(context_results)
            company_context = build_company_context(vector_context, company_settings)

            system_tpl = load_prompt("system")
            system_base = system_tpl.render_system(
                company_context=company_context,
                deal_criteria=company_settings.get("deal_criteria", ""),
            )

            # Render prompt with all accumulated analysis results
            tpl = load_prompt("final_verdict")
            system_prompt, user_prompt = tpl.render(
                system_base=system_base,
                structured_deal=structured_deal,
                scores=state.get("scores", []),
                total_score=state.get("total_score", 0.0),
                verdict=state.get("verdict", "pending"),
                resource_estimate=state.get("resource_estimate", {}),
                risks=state.get("risks", []),
                risk_interdependencies=state.get("risk_interdependencies", []),
                similar_projects=state.get("similar_projects", []),
            )

            # LLM returns raw markdown (not JSON)
            deal_id = uuid.UUID(state["deal_id"])
            markdown, _log_id = await logged_call_llm(
                system_prompt,
                user_prompt,
                deal_id=deal_id,
                node_name="final_verdict",
            )

            return {"final_report": markdown, "status": "completed"}

        except Exception:
            logger.exception("final_verdict node failed")
            return {
                "final_report": "",
                "errors": ["final_verdict: node execution failed"],
                "status": "failed",
            }

    return final_verdict_node
