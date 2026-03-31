"""Final verdict ReAct worker — generate executive markdown report."""

import logging
import uuid

from backend.app.agent.llm import get_llm
from backend.app.agent.prompt_loader import load_prompt
from backend.app.agent.state import AgentState
from backend.app.agent.tools import calculate_roi, calculate_weighted_score
from backend.app.agent.workers.base_worker import invoke_worker, make_react_worker

logger = logging.getLogger(__name__)

TOOLS = [calculate_weighted_score, calculate_roi]

_REACT_INSTRUCTIONS = """

## 사용 가능 도구
- calculate_weighted_score: 가중 점수 재검증
- calculate_roi: ROI 수치 재검증

## 작업 지침
1. 모든 분석 결과를 종합적으로 검토하세요.
2. 필요시 도구로 점수와 ROI를 재검증하세요.
3. 최종 보고서를 마크다운 형식으로 작성하세요.

## 출력 형식
마크다운 형식의 최종 보고서 (JSON이 아님). 보고서 구조는 프롬프트의 지시를 따르세요.
"""


def make_final_verdict_worker_node():
    """Factory — returns an async final-verdict node (markdown output)."""

    async def final_verdict_node(state: AgentState) -> dict:
        try:
            structured_deal = state.get("structured_deal", {})
            deal_id = uuid.UUID(state["deal_id"])

            # Render prompts with all accumulated analysis results
            system_tpl = load_prompt("system")
            system_base = system_tpl.render_system(
                company_context="",
                deal_criteria="",
            )

            tpl = load_prompt("final_verdict")
            system_prompt = tpl.render_system(system_base=system_base)
            user_prompt = tpl.render_user(
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

            llm = get_llm()
            worker = make_react_worker(
                name="final_verdict",
                llm=llm,
                tools=TOOLS,
                system_prompt=system_prompt + _REACT_INSTRUCTIONS,
            )

            # Output is raw markdown — no JSON parsing
            markdown = await invoke_worker(
                worker,
                user_prompt,
                deal_id=deal_id,
                worker_name="final_verdict",
            )

            return {"final_report": markdown, "status": "completed"}

        except Exception:
            logger.exception("final_verdict worker failed")
            return {
                "final_report": "",
                "errors": ["final_verdict: worker execution failed"],
                "status": "failed",
            }

    return final_verdict_node
