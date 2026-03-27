"""Deal structuring node — extract structured fields from raw deal text."""

import logging
import uuid

from backend.app.agent.base import (
    build_company_context,
    fetch_company_settings,
    format_company_context,
    logged_call_llm,
    parse_json_response,
    update_log_parsed_output,
)
from backend.app.agent.prompt_loader import load_prompt
from backend.app.agent.state import AgentState
from backend.app.db.session import AsyncSessionLocal
from backend.app.db.vector_store import CompanyContextStore

logger = logging.getLogger(__name__)

_UNIT_TO_MANWON: dict[str, float] = {
    "원": 1 / 10_000,
    "만원": 1,
    "억원": 10_000,
}


def _normalize_amount_to_manwon(structured: dict) -> dict:
    """Convert expected_amount to 만원 units and pin amount_unit = '만원'.

    Eliminates downstream LLM unit-conversion errors by normalizing at the
    code level immediately after deal structuring.
    """
    amount = structured.get("expected_amount")
    unit = structured.get("amount_unit", "만원")
    if amount is None:
        return structured
    factor = _UNIT_TO_MANWON.get(unit, 1)
    return {**structured, "expected_amount": round(amount * factor), "amount_unit": "만원"}


def make_deal_structuring_node(
    context_store: CompanyContextStore,
):
    """Factory — returns an async node function with injected dependencies."""

    async def deal_structuring_node(state: AgentState) -> dict:
        try:
            deal_input = state["deal_input"]

            # Fetch context for the system prompt (own session for concurrency safety)
            async with AsyncSessionLocal() as db:
                company_settings = await fetch_company_settings(db)

            context_results = await context_store.query(deal_input, top_k=5)
            vector_context = format_company_context(context_results)

            company_context = build_company_context(vector_context, company_settings)

            # Render prompts
            system_tpl = load_prompt("system")
            system_base = system_tpl.render_system(
                company_context=company_context,
                deal_criteria=company_settings.get("deal_criteria", ""),
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
            normalized = _normalize_amount_to_manwon(structured)
            await update_log_parsed_output(log_id, normalized)

            return {"structured_deal": normalized, "status": "deal_structured"}

        except Exception:
            logger.exception("deal_structuring node failed")
            return {
                "structured_deal": {},
                "errors": ["deal_structuring: node execution failed"],
                "status": "failed",
            }

    return deal_structuring_node
