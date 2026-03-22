"""Similar project node — find and analyse comparable past projects."""

import json
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
from backend.app.db.vector_store import CompanyContextStore, ProjectHistoryStore

logger = logging.getLogger(__name__)


def make_similar_project_node(
    project_store: ProjectHistoryStore,
    context_store: CompanyContextStore,
):
    """Factory — returns an async similar-project node."""

    async def similar_project_node(state: AgentState) -> dict:
        try:
            structured_deal = state.get("structured_deal", {})

            # Build a search query from structured deal fields
            overview = structured_deal.get("project_overview", {})
            if isinstance(overview, dict):
                overview_text = " ".join(
                    filter(None, [overview.get("objective", ""), overview.get("scope", "")]),
                )
            else:
                overview_text = str(overview) if overview else ""
            parts = [
                overview_text,
                " ".join(structured_deal.get("tech_requirements", [])),
                structured_deal.get("customer_industry", ""),
            ]
            query_text = " ".join(p for p in parts if p).strip()
            if not query_text:
                return {"similar_projects": []}

            # Search Pinecone for similar projects
            past_projects = await project_store.search_similar(
                query_text,
                top_k=3,
                industry=structured_deal.get("customer_industry"),
            )

            # If no results, skip LLM call
            if not past_projects:
                return {"similar_projects": []}

            # Build system base prompt with company context
            async with AsyncSessionLocal() as db:
                company_settings = await fetch_company_settings(db)

            context_results = await context_store.query(query_text, top_k=5)
            vector_context = format_company_context(context_results)
            company_context = build_company_context(vector_context, company_settings)

            system_tpl = load_prompt("system")
            system_base = system_tpl.render_system(
                company_context=company_context,
                deal_criteria=company_settings.get("deal_criteria", ""),
            )

            # Render prompt for LLM-enhanced analysis
            tpl = load_prompt("similar_project")
            system_prompt, user_prompt = tpl.render(
                system_base=system_base,
                structured_deal=structured_deal,
                past_projects=json.dumps(past_projects, ensure_ascii=False),
            )

            deal_id = uuid.UUID(state["deal_id"])
            raw, log_id = await logged_call_llm(
                system_prompt,
                user_prompt,
                deal_id=deal_id,
                node_name="similar_project",
            )
            parsed = parse_json_response(raw)
            await update_log_parsed_output(log_id, parsed)

            return {"similar_projects": parsed.get("similar_projects", past_projects)}

        except Exception:
            logger.exception("similar_project node failed")
            return {
                "similar_projects": [],
                "errors": ["similar_project: node execution failed"],
            }

    return similar_project_node
