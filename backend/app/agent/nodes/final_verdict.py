"""Final verdict node — generate executive markdown report."""

import json
import logging

from backend.app.agent.base import call_llm
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
                scores=json.dumps(state.get("scores", []), ensure_ascii=False),
                total_score=state.get("total_score", 0.0),
                verdict=state.get("verdict", "pending"),
                resource_estimate=json.dumps(state.get("resource_estimate", {}), ensure_ascii=False),
                risks=json.dumps(state.get("risks", []), ensure_ascii=False),
                similar_projects=json.dumps(state.get("similar_projects", []), ensure_ascii=False),
            )

            # LLM returns raw markdown (not JSON)
            markdown = await call_llm(system_prompt, user_prompt)

            return {"final_report": markdown, "status": "completed"}

        except Exception:
            logger.exception("final_verdict node failed")
            return {
                "final_report": "",
                "errors": ["final_verdict: node execution failed"],
                "status": "failed",
            }

    return final_verdict_node
