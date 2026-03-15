"""Analysis service — orchestrates graph execution and DB persistence."""

import logging
import uuid

from backend.app.agent.graph import build_graph
from backend.app.db.repositories import analysis_repo, deal_repo
from backend.app.db.session import AsyncSessionLocal

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


class AnalysisService:
    """Run the full deal-analysis pipeline and persist results."""

    async def run_analysis(self, deal_id: uuid.UUID) -> None:
        """Execute the LangGraph pipeline for *deal_id* and save results.

        Creates its own DB session because this method runs inside
        ``BackgroundTasks`` (outside the request lifecycle).
        """
        logger.info("run_analysis started for deal %s", deal_id)
        async with AsyncSessionLocal() as db:
            try:
                deal = await deal_repo.get_by_id(db, deal_id)
                if deal is None:
                    logger.error("Deal %s not found — skipping analysis", deal_id)
                    return

                # Build and run the graph
                logger.info("Building graph for deal %s", deal_id)
                graph = build_graph(db)
                logger.info("Graph built, starting execution for deal %s", deal_id)

                result: dict = {}
                async for event in graph.astream(
                    {"deal_input": deal.raw_input or "", "deal_id": str(deal_id)},
                ):
                    for node_name, node_output in event.items():
                        result.update(node_output)
                        label = STEP_LABELS.get(node_name)
                        if label:
                            logger.info("Deal %s: completed step '%s'", deal_id, node_name)
                            deal.current_step = label
                            await db.commit()

                # Persist analysis result
                await analysis_repo.create(
                    db,
                    deal_id=deal_id,
                    total_score=result.get("total_score"),
                    verdict=result.get("verdict"),
                    scores=result.get("scores"),
                    resource_estimate=result.get("resource_estimate"),
                    risks=result.get("risks"),
                    similar_projects=result.get("similar_projects"),
                    report_markdown=result.get("final_report"),
                )

                # Update deal structured_data and status
                if result.get("structured_deal"):
                    deal.structured_data = result["structured_deal"]
                deal.current_step = None
                await deal_repo.update_status(db, deal_id, "completed")

                await db.commit()
                logger.info("Analysis completed for deal %s", deal_id)

            except Exception:
                logger.exception("Analysis failed for deal %s", deal_id)
                await db.rollback()
                # Mark deal as failed using a fresh session
                try:
                    async with AsyncSessionLocal() as err_db:
                        err_deal = await deal_repo.get_by_id(err_db, deal_id)
                        if err_deal is not None:
                            err_deal.current_step = None
                        await deal_repo.update_status(err_db, deal_id, "failed")
                        await err_db.commit()
                except Exception:
                    logger.exception("Failed to update deal %s status to 'failed'", deal_id)
