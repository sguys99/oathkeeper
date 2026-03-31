"""Resource estimation ReAct worker — calculate team, duration, and cost."""

import logging
import uuid

from backend.app.agent.base import parse_json_response
from backend.app.agent.llm import get_llm
from backend.app.agent.prompt_loader import load_prompt
from backend.app.agent.state import AgentState
from backend.app.agent.tools import (
    calculate_roi,
    estimate_timeline,
    get_company_settings,
    get_team_members,
    search_similar_projects,
)
from backend.app.agent.workers.base_worker import invoke_worker, make_react_worker

logger = logging.getLogger(__name__)

TOOLS = [
    get_team_members,
    get_company_settings,
    search_similar_projects,
    estimate_timeline,
    calculate_roi,
]

_REACT_INSTRUCTIONS = """

## 사용 가능 도구
- get_team_members: 팀원 정보 및 가용성 조회
- get_company_settings: 회사 설정 (사업 방향, 단가 등) 조회
- search_similar_projects: 유사 프로젝트 검색 (참조 견적)
- estimate_timeline: PERT 기반 일정 시뮬레이션
- calculate_roi: ROI, 손익분기점, 수익성 계산

## 작업 지침
1. 팀원 정보(get_team_members)와 회사 설정(get_company_settings)을 조회하세요.
2. 유사 프로젝트(search_similar_projects)를 참조하여 견적의 현실성을 검증하세요.
3. estimate_timeline으로 일정을 추정하고, calculate_roi로 수익성을 검증하세요.
4. 비현실적인 추정이 나오면 파라미터를 조정하여 재추정하세요.

## 출력 형식
JSON: work_breakdown, phases, team_composition, cost_breakdown,
profitability 등을 포함한 상세 리소스 견적
"""


def make_resource_estimation_worker_node(parent_log_id: uuid.UUID | None = None):
    """Factory — returns an async resource-estimation node."""

    async def resource_estimation_node(state: AgentState) -> dict:
        try:
            structured_deal = state.get("structured_deal", {})
            deal_id = uuid.UUID(state["deal_id"])

            # Render prompts
            system_tpl = load_prompt("system")
            system_base = system_tpl.render_system(
                company_context="",
                deal_criteria="",
            )

            tpl = load_prompt("resource_estimation")
            system_prompt = tpl.render_system(system_base=system_base)
            user_prompt = tpl.render_user(
                system_base=system_base,
                structured_deal=structured_deal,
                team_members=[],  # Worker fetches via tools
                company_rates="",
                past_projects=[],
            )

            llm = get_llm()
            worker = make_react_worker(
                name="resource_estimation",
                llm=llm,
                tools=TOOLS,
                system_prompt=system_prompt + _REACT_INSTRUCTIONS,
            )

            raw_result = await invoke_worker(
                worker,
                user_prompt,
                deal_id=deal_id,
                worker_name="resource_estimation",
                parent_log_id=parent_log_id,
            )

            parsed = parse_json_response(raw_result)
            return {"resource_estimate": parsed}

        except Exception:
            logger.exception("resource_estimation worker failed")
            return {
                "resource_estimate": {},
                "errors": ["resource_estimation: worker execution failed"],
            }

    return resource_estimation_node
