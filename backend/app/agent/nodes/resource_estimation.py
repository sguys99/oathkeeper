"""Resource estimation node — calculate team, duration, and cost."""

import logging
import uuid

from backend.app.agent.base import (
    build_company_context,
    fetch_company_settings,
    format_company_context,
    format_team_members,
    logged_call_llm,
    parse_json_response,
    update_log_parsed_output,
)
from backend.app.agent.prompt_loader import load_prompt
from backend.app.agent.state import AgentState
from backend.app.db.repositories import settings_repo
from backend.app.db.session import AsyncSessionLocal
from backend.app.db.vector_store import CompanyContextStore, ProjectHistoryStore

logger = logging.getLogger(__name__)


def make_resource_estimation_node(
    project_store: ProjectHistoryStore,
    context_store: CompanyContextStore,
):
    """Factory — returns an async resource-estimation node."""

    async def resource_estimation_node(state: AgentState) -> dict:
        try:
            structured_deal = state.get("structured_deal", {})

            # Fetch team members and company rates from DB (own session for concurrency safety)
            async with AsyncSessionLocal() as db:
                members = await settings_repo.list_team_members(db)
                team_members = format_team_members(members)

                rates_setting = await settings_repo.get_setting(db, "company_rates")
                company_rates = rates_setting.value if rates_setting else ""

                company_settings = await fetch_company_settings(db)

            # Fetch similar past projects for reference
            deal_text = structured_deal.get("project_summary", "")
            past_projects = await project_store.search_similar(deal_text, top_k=3)

            # Build system base prompt with company context
            context_results = await context_store.query(deal_text, top_k=5)
            vector_context = format_company_context(context_results)
            company_context = build_company_context(vector_context, company_settings)

            system_tpl = load_prompt("system")
            system_base = system_tpl.render_system(
                company_context=company_context,
                deal_criteria=company_settings.get("deal_criteria", ""),
            )

            # Render prompts
            tpl = load_prompt("resource_estimation")
            system_prompt, user_prompt = tpl.render(
                system_base=system_base,
                structured_deal=structured_deal,
                team_members=team_members,
                company_rates=company_rates,
                past_projects=past_projects,
            )

            deal_id = uuid.UUID(state["deal_id"])
            raw, log_id = await logged_call_llm(
                system_prompt,
                user_prompt,
                deal_id=deal_id,
                node_name="resource_estimation",
            )
            parsed = parse_json_response(raw)
            await update_log_parsed_output(log_id, parsed)

            return {"resource_estimate": parsed}

        except Exception:
            logger.exception("resource_estimation node failed")
            return {
                "resource_estimate": {},
                "errors": ["resource_estimation: node execution failed"],
            }

    return resource_estimation_node
