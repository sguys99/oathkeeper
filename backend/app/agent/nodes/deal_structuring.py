"""Deal structuring node — extract structured fields from raw deal text."""

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


def make_deal_structuring_node(
    context_store: CompanyContextStore,
):
    """Factory — returns an async node function with injected dependencies."""

    async def deal_structuring_node(state: AgentState) -> dict:
        try:
            deal_input = state["deal_input"]

            # Fetch context for the system prompt (own session for concurrency safety)
            async with AsyncSessionLocal() as db:
                criteria = await settings_repo.list_active_criteria(db)
                company_settings = await fetch_company_settings(db)
            scoring_criteria = format_scoring_criteria(criteria)

            context_results = await context_store.query(deal_input, top_k=5)
            vector_context = format_company_context(context_results)

            company_context = build_company_context(vector_context, company_settings)

            # Render prompts
            system_tpl = load_prompt("system")
            system_base = system_tpl.render_system(
                company_context=company_context,
                deal_criteria=company_settings.get("deal_criteria", ""),
                scoring_criteria=scoring_criteria,
            )

            tpl = load_prompt("deal_structuring")
            system_prompt, user_prompt = tpl.render(
                system_base=system_base,
                deal_input=deal_input,
            )

            # Call LLM and parse
            deal_id = uuid.UUID(state["deal_id"])
            raw, log_id = await logged_call_llm(
                system_prompt,
                user_prompt,
                deal_id=deal_id,
                node_name="deal_structuring",
            )
            structured = parse_json_response(raw)
            await update_log_parsed_output(log_id, structured)

            return {"structured_deal": structured, "status": "deal_structured"}

        except Exception:
            logger.exception("deal_structuring node failed")
            return {
                "structured_deal": {},
                "errors": ["deal_structuring: node execution failed"],
                "status": "failed",
            }

    return deal_structuring_node
