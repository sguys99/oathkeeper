"""Similar project ReAct worker — find and analyse comparable past projects."""

import logging
import uuid

from backend.app.agent.base import log_node_skip, parse_json_response
from backend.app.agent.llm import get_llm
from backend.app.agent.prompt_loader import load_prompt
from backend.app.agent.state import AgentState
from backend.app.agent.tools import (
    get_past_deal_analysis,
    search_company_context,
    search_similar_projects,
)
from backend.app.agent.workers.base_worker import invoke_worker, make_react_worker

logger = logging.getLogger(__name__)

TOOLS = [search_similar_projects, get_past_deal_analysis, search_company_context]

_REACT_INSTRUCTIONS = """

## 사용 가능 도구
- search_similar_projects: 유사 프로젝트 벡터 검색 (산업군 필터 지원)
- get_past_deal_analysis: 과거 딜의 전체 분석 결과 조회
- search_company_context: 프로젝트 교훈 및 회사 컨텍스트 검색

## 작업 지침
1. search_similar_projects로 유사 프로젝트를 검색하세요.
2. 유사도가 높은 프로젝트에 대해 get_past_deal_analysis로 상세 분석을 조회하세요.
3. 성공/실패 요인, 교훈, 현재 딜에 대한 시사점을 분석하세요.

## 출력 형식
JSON: {"similar_projects": [{"project_name": str,
"relevance_score": float, "key_comparisons": [...],
"lessons_learned": [...], "risk_implications": [...]}]}
"""


def _build_search_query(structured_deal: dict) -> str:
    """Build a composite search query from structured deal fields."""
    overview = structured_deal.get("project_overview", {})
    if isinstance(overview, dict):
        overview_text = " ".join(
            filter(None, [overview.get("objective", ""), overview.get("scope", "")]),
        )
    else:
        overview_text = str(overview) if overview else ""
    tech_reqs = structured_deal.get("tech_requirements") or []
    if isinstance(tech_reqs, str):
        tech_reqs = [tech_reqs]
    parts = [
        overview_text,
        " ".join(tech_reqs),
        structured_deal.get("customer_industry", ""),
    ]
    return " ".join(p for p in parts if p).strip()


def make_similar_project_worker_node():
    """Factory — returns an async similar-project node with skip logic."""

    async def similar_project_node(state: AgentState) -> dict:
        try:
            deal_id = uuid.UUID(state["deal_id"])
            structured_deal = state.get("structured_deal", {})

            # Check if we can build a search query
            query_text = _build_search_query(structured_deal)
            if not query_text:
                await log_node_skip(
                    deal_id=deal_id,
                    node_name="similar_project",
                    reason="검색 쿼리를 생성할 수 없음 (빈 필드)",
                )
                return {"similar_projects": []}

            # Render prompts
            system_tpl = load_prompt("system")
            system_base = system_tpl.render_system(
                company_context="",
                deal_criteria="",
            )

            tpl = load_prompt("similar_project")
            system_prompt = tpl.render_system(system_base=system_base)
            user_prompt = tpl.render_user(
                system_base=system_base,
                structured_deal=structured_deal,
                past_projects=[],  # Worker searches via tools
            )

            llm = get_llm()
            worker = make_react_worker(
                name="similar_project",
                llm=llm,
                tools=TOOLS,
                system_prompt=system_prompt + _REACT_INSTRUCTIONS,
            )

            raw_result = await invoke_worker(
                worker,
                user_prompt,
                deal_id=deal_id,
                worker_name="similar_project",
            )

            parsed = parse_json_response(raw_result)
            return {"similar_projects": parsed.get("similar_projects", [])}

        except Exception as exc:
            logger.exception("similar_project worker failed")
            deal_id_for_log = None
            try:
                deal_id_for_log = uuid.UUID(state["deal_id"])
            except Exception:
                pass
            if deal_id_for_log:
                await log_node_skip(
                    deal_id=deal_id_for_log,
                    node_name="similar_project",
                    reason="워커 실행 실패",
                    error=str(exc),
                )
            return {
                "similar_projects": [],
                "errors": ["similar_project: worker execution failed"],
            }

    return similar_project_node
