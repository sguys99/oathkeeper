"""Deal structuring node — extract structured fields from raw deal text."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agent.base import (
    call_llm,
    format_company_context,
    format_scoring_criteria,
    parse_json_response,
)
from backend.app.agent.prompt_loader import load_prompt
from backend.app.agent.state import AgentState
from backend.app.db.repositories import settings_repo
from backend.app.db.vector_store import CompanyContextStore

logger = logging.getLogger(__name__)


def make_deal_structuring_node(
    db: AsyncSession,
    context_store: CompanyContextStore,
):
    """Factory — returns an async node function with injected dependencies."""

    async def deal_structuring_node(state: AgentState) -> dict:
        try:
            deal_input = state["deal_input"]

            # Fetch context for the system prompt
            criteria = await settings_repo.list_active_criteria(db)
            scoring_criteria = format_scoring_criteria(criteria)

            context_results = await context_store.query(deal_input, top_k=5)
            company_context = format_company_context(context_results)

            # Render prompts
            system_tpl = load_prompt("system")
            system_base = system_tpl.render_system(
                company_context=company_context,
                deal_criteria="",
                scoring_criteria=scoring_criteria,
            )

            tpl = load_prompt("deal_structuring")
            system_prompt, user_prompt = tpl.render(
                system_base=system_base,
                deal_input=deal_input,
            )

            # Call LLM and parse
            raw = await call_llm(system_prompt, user_prompt)
            structured = parse_json_response(raw)

            return {"structured_deal": structured, "status": "deal_structured"}

        except Exception:
            logger.exception("deal_structuring node failed")
            return {
                "structured_deal": {},
                "errors": ["deal_structuring: node execution failed"],
                "status": "failed",
            }

    return deal_structuring_node
