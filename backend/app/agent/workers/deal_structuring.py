"""Deal structuring ReAct worker — extract structured fields with autonomous data gathering."""

import logging
import uuid

from backend.app.agent.base import normalize_amount_to_manwon, parse_json_response
from backend.app.agent.llm import get_llm
from backend.app.agent.prompt_loader import load_prompt
from backend.app.agent.state import AgentState
from backend.app.agent.tools import fetch_notion_deal, format_currency, search_company_context
from backend.app.agent.workers.base_worker import (
    invoke_worker,
    make_react_worker,
)

logger = logging.getLogger(__name__)

TOOLS = [search_company_context, fetch_notion_deal, format_currency]

_REACT_INSTRUCTIONS = """

## 사용 가능 도구
다음 도구를 필요에 따라 활용하여 정확한 구조화를 수행하세요:
- search_company_context: 회사 맥락 검색 (산업별 추출 규칙, 사업 방향 등)
- fetch_notion_deal: Notion에서 딜 상세 정보 조회
- format_currency: 금액 단위 변환

## 작업 지침
1. 먼저 입력 텍스트를 분석하여 누락된 정보가 있는지 파악하세요.
2. 필요하다면 도구를 사용하여 추가 정보를 수집하세요.
3. 최종적으로 구조화된 JSON 결과를 반환하세요.

## 출력 형식
모든 정보를 수집한 후, 마크다운 코드 펜스 없이 단일 JSON 객체로 응답하세요.
"""


def make_deal_structuring_worker_node():
    """Factory — returns an async node function for AgentState."""

    async def deal_structuring_node(state: AgentState) -> dict:
        try:
            deal_input = state["deal_input"]
            deal_id = uuid.UUID(state["deal_id"])

            # Render system prompt from existing YAML templates
            system_tpl = load_prompt("system")
            system_base = system_tpl.render_system(
                company_context="",  # Worker fetches via tools
                deal_criteria="",
            )

            tpl = load_prompt("deal_structuring")
            system_prompt = tpl.render_system(system_base=system_base)
            user_prompt = tpl.render_user(
                system_base=system_base,
                deal_input=deal_input,
            )

            # Build and invoke worker
            llm = get_llm()
            worker = make_react_worker(
                name="deal_structuring",
                llm=llm,
                tools=TOOLS,
                system_prompt=system_prompt + _REACT_INSTRUCTIONS,
            )

            raw_result = await invoke_worker(
                worker,
                user_prompt,
                deal_id=deal_id,
                worker_name="deal_structuring",
            )

            # Parse and apply business logic
            structured = parse_json_response(raw_result)
            normalized = normalize_amount_to_manwon(structured)

            return {"structured_deal": normalized, "status": "deal_structured"}

        except Exception:
            logger.exception("deal_structuring worker failed")
            return {
                "structured_deal": {},
                "errors": ["deal_structuring: worker execution failed"],
                "status": "failed",
            }

    return deal_structuring_node
