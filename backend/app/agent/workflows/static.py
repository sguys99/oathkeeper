"""Static workflow — deterministic two-phase LangGraph StateGraph execution."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable

from backend.app.agent.graph import build_graph

logger = logging.getLogger(__name__)

STEP_LABELS: dict[str, str] = {
    "deal_structuring": "Deal 구조화 중...",
    "scoring": "평가 기준 분석 중...",
    "resource_estimation": "리소스 추정 중...",
    "risk_analysis": "리스크 분석 중...",
    "similar_project": "유사 프로젝트 검색 중...",
    "final_verdict": "최종 판정 중...",
    "hold_verdict": "보류 판정 중...",
}


class StaticWorkflow:
    """Execute the static two-phase LangGraph pipeline."""

    async def execute(
        self,
        deal_id: uuid.UUID,
        deal_input: str,
        on_progress: Callable[[str], Awaitable[None]],
    ) -> dict:
        logger.info("Building static graph for deal %s", deal_id)
        graph = build_graph()

        result: dict = {}
        async for event in graph.astream(
            {"deal_input": deal_input, "deal_id": str(deal_id)},
        ):
            for node_name, node_output in event.items():
                if node_output is not None:
                    result.update(node_output)
                label = STEP_LABELS.get(node_name)
                if label:
                    logger.info("Deal %s: completed step '%s'", deal_id, node_name)
                    await on_progress(label)

        return result
