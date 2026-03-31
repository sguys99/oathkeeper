"""Scoring ReAct worker — evaluate deal against criteria with tool-assisted analysis."""

import logging
import uuid

from backend.app.agent.base import (
    determine_verdict,
    parse_json_response,
    recalculate_scores,
)
from backend.app.agent.llm import get_llm
from backend.app.agent.prompt_loader import load_prompt
from backend.app.agent.state import AgentState
from backend.app.agent.tools import (
    calculate_weighted_score,
    get_scoring_criteria,
    search_company_context,
    search_similar_projects,
)
from backend.app.agent.workers.base_worker import invoke_worker, make_react_worker

logger = logging.getLogger(__name__)

TOOLS = [get_scoring_criteria, search_company_context, calculate_weighted_score, search_similar_projects]

_REACT_INSTRUCTIONS = """

## 사용 가능 도구
- get_scoring_criteria: 평가 기준과 가중치 조회
- search_company_context: 회사 전략/맥락 검색
- calculate_weighted_score: 가중 점수 정밀 계산 (수동 계산 금지, 반드시 이 도구 사용)
- search_similar_projects: 유사 프로젝트 검색하여 비교 기반 평가

## 작업 지침
1. 먼저 평가 기준(get_scoring_criteria)을 조회하세요.
2. 필요시 회사 컨텍스트와 유사 프로젝트를 참조하세요.
3. 각 기준별로 0-100점 평가 후, calculate_weighted_score로 최종 점수를 계산하세요.
4. 가중 점수를 수동으로 계산하지 마세요.

## 출력 형식
JSON: {"scores": [{"criterion": str, "score": float, "weight": float,
"rationale": str}, ...], "total_score": float, "verdict": str}
"""


def make_scoring_worker_node(parent_log_id: uuid.UUID | None = None):
    """Factory — returns an async scoring node with post-processing."""

    async def scoring_node(state: AgentState) -> dict:
        try:
            structured_deal = state.get("structured_deal", {})
            resource_estimate = state.get("resource_estimate", {})
            deal_id = uuid.UUID(state["deal_id"])

            # Render prompts
            system_tpl = load_prompt("system")
            system_base = system_tpl.render_system(
                company_context="",
                deal_criteria="",
            )

            tpl = load_prompt("scoring")
            system_prompt = tpl.render_system(system_base=system_base)
            user_prompt = tpl.render_user(
                system_base=system_base,
                structured_deal=structured_deal,
                scoring_criteria=[],  # Worker fetches via tools
                resource_estimate=resource_estimate,
            )

            llm = get_llm()
            worker = make_react_worker(
                name="scoring",
                llm=llm,
                tools=TOOLS,
                system_prompt=system_prompt + _REACT_INSTRUCTIONS,
            )

            raw_result = await invoke_worker(
                worker,
                user_prompt,
                deal_id=deal_id,
                worker_name="scoring",
                parent_log_id=parent_log_id,
            )

            parsed = parse_json_response(raw_result)

            # Server-side recalculation — overrides LLM arithmetic
            scores, total_score = recalculate_scores(parsed.get("scores", []))
            verdict = determine_verdict(total_score)

            return {
                "scores": scores,
                "total_score": total_score,
                "verdict": verdict,
            }

        except Exception:
            logger.exception("scoring worker failed")
            return {
                "scores": [],
                "total_score": 0.0,
                "verdict": "pending",
                "errors": ["scoring: worker execution failed"],
            }

    return scoring_node
