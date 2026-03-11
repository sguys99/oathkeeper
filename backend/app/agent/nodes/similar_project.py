"""Similar project node — find and analyse comparable past projects."""

import json
import logging

from backend.app.agent.base import call_llm, parse_json_response
from backend.app.agent.prompt_loader import load_prompt
from backend.app.agent.state import AgentState
from backend.app.db.vector_store import ProjectHistoryStore

logger = logging.getLogger(__name__)


def make_similar_project_node(project_store: ProjectHistoryStore):
    """Factory — returns an async similar-project node."""

    async def similar_project_node(state: AgentState) -> dict:
        try:
            structured_deal = state.get("structured_deal", {})

            # Build a search query from structured deal fields
            parts = [
                structured_deal.get("project_summary", ""),
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

            # Render prompt for LLM-enhanced analysis
            tpl = load_prompt("similar_project")
            system_prompt, user_prompt = tpl.render(
                structured_deal=structured_deal,
                past_projects=json.dumps(past_projects, ensure_ascii=False),
            )

            raw = await call_llm(system_prompt, user_prompt)
            parsed = parse_json_response(raw)

            return {"similar_projects": parsed.get("similar_projects", past_projects)}

        except Exception:
            logger.exception("similar_project node failed")
            return {
                "similar_projects": [],
                "errors": ["similar_project: node execution failed"],
            }

    return similar_project_node
