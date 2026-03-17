"""Final verdict node — generate executive markdown report."""

import logging
import uuid

from backend.app.agent.base import logged_call_llm
from backend.app.agent.prompt_loader import load_prompt
from backend.app.agent.state import AgentState

logger = logging.getLogger(__name__)


def make_final_verdict_node():
    """Factory — returns an async final-verdict node."""

    async def final_verdict_node(state: AgentState) -> dict:
        try:
            # Render prompt with all accumulated analysis results
            tpl = load_prompt("final_verdict")
            system_prompt, user_prompt = tpl.render(
                structured_deal=state.get("structured_deal", {}),
                scores=state.get("scores", []),
                total_score=state.get("total_score", 0.0),
                verdict=state.get("verdict", "pending"),
                resource_estimate=state.get("resource_estimate", {}),
                risks=state.get("risks", []),
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
