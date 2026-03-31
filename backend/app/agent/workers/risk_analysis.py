"""Risk analysis ReAct worker — identify risks across 5 categories."""

import logging
import uuid

from backend.app.agent.base import parse_json_response
from backend.app.agent.llm import get_llm
from backend.app.agent.prompt_loader import load_prompt
from backend.app.agent.state import AgentState
from backend.app.agent.tools import (
    assess_risk_matrix,
    search_company_context,
    search_similar_projects,
    web_search,
)
from backend.app.agent.workers.base_worker import invoke_worker, make_react_worker

logger = logging.getLogger(__name__)

TOOLS = [search_company_context, web_search, assess_risk_matrix, search_similar_projects]

_REACT_INSTRUCTIONS = """

## 사용 가능 도구
- search_company_context: 회사 컨텍스트에서 알려진 리스크 패턴 검색
- web_search: 시장/기술 동향, 경쟁사 정보 등 외부 리스크 요인 검색
- assess_risk_matrix: 확률×영향도 매트릭스 계산 (리스크 등급 자동 산정)
- search_similar_projects: 과거 프로젝트의 리스크 데이터 참조

## 작업 지침
1. 구조화된 딜 데이터와 리소스 견적을 분석하여 잠재 리스크를 식별하세요.
2. 필요시 회사 컨텍스트와 외부 정보를 검색하세요.
3. assess_risk_matrix를 사용하여 리스크 등급을 계산하세요.
4. 각 카테고리별 1-3개, 전체 5-15개 리스크를 도출하세요.

## 출력 형식
JSON: {"risks": [...], "risk_interdependencies": [...]}
"""


def make_risk_analysis_worker_node():
    """Factory — returns an async risk-analysis node."""

    async def risk_analysis_node(state: AgentState) -> dict:
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

            tpl = load_prompt("risk_analysis")
            system_prompt = tpl.render_system(system_base=system_base)
            user_prompt = tpl.render_user(
                system_base=system_base,
                structured_deal=structured_deal,
                resource_estimate=resource_estimate,
            )

            llm = get_llm()
            worker = make_react_worker(
                name="risk_analysis",
                llm=llm,
                tools=TOOLS,
                system_prompt=system_prompt + _REACT_INSTRUCTIONS,
            )

            raw_result = await invoke_worker(
                worker,
                user_prompt,
                deal_id=deal_id,
                worker_name="risk_analysis",
            )

            parsed = parse_json_response(raw_result)
            return {
                "risks": parsed.get("risks", []),
                "risk_interdependencies": parsed.get("risk_interdependencies", []),
            }

        except Exception:
            logger.exception("risk_analysis worker failed")
            return {
                "risks": [],
                "errors": ["risk_analysis: worker execution failed"],
            }

    return risk_analysis_node
