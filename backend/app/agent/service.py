"""Analysis service — orchestrates graph execution and DB persistence."""

import logging
import uuid

from backend.app.agent.graph import build_graph
from backend.app.db.repositories import analysis_repo, deal_repo
from backend.app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


class AnalysisService:
    """Run the full deal-analysis pipeline and persist results."""

    async def run_analysis(self, deal_id: uuid.UUID) -> None:
        """Execute the LangGraph pipeline for *deal_id* and save results.

        Creates its own DB session because this method runs inside
        ``BackgroundTasks`` (outside the request lifecycle).
        """
        async with AsyncSessionLocal() as db:
            try:
                deal = await deal_repo.get_by_id(db, deal_id)
                if deal is None:
                    logger.error("Deal %s not found — skipping analysis", deal_id)
                    return

                # Build and run the graph
                graph = build_graph(db)
                result = await graph.ainvoke({"deal_input": deal.raw_input or ""})

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
                await deal_repo.update_status(db, deal_id, "completed")

                await db.commit()
                logger.info("Analysis completed for deal %s", deal_id)

            except Exception:
                logger.exception("Analysis failed for deal %s", deal_id)
                await db.rollback()
                # Mark deal as failed using a fresh session
                try:
                    async with AsyncSessionLocal() as err_db:
                        await deal_repo.update_status(err_db, deal_id, "failed")
                        await err_db.commit()
                except Exception:
                    logger.exception("Failed to update deal %s status to 'failed'", deal_id)
