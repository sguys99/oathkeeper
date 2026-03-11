"""Risk analysis node — identify risks across 5 categories."""

import logging

from backend.app.agent.base import (
    call_llm,
    format_company_context,
    parse_json_response,
)
from backend.app.agent.prompt_loader import load_prompt
from backend.app.agent.state import AgentState
from backend.app.db.vector_store import CompanyContextStore

logger = logging.getLogger(__name__)


def make_risk_analysis_node(context_store: CompanyContextStore):
    """Factory — returns an async risk-analysis node."""

    async def risk_analysis_node(state: AgentState) -> dict:
        try:
            structured_deal = state.get("structured_deal", {})

            # Fetch company context
            query_text = structured_deal.get("project_summary", "")
            context_results = await context_store.query(query_text, top_k=5)
            company_context = format_company_context(context_results)

            # Render prompts
            tpl = load_prompt("risk_analysis")
            system_prompt, user_prompt = tpl.render(
                structured_deal=structured_deal,
                company_context=company_context,
            )

            raw = await call_llm(system_prompt, user_prompt)
            parsed = parse_json_response(raw)

            return {"risks": parsed.get("risks", [])}

        except Exception:
            logger.exception("risk_analysis node failed")
            return {
                "risks": [],
                "errors": ["risk_analysis: node execution failed"],
            }

    return risk_analysis_node
