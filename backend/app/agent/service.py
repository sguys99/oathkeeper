"""Analysis service — orchestrates graph execution and DB persistence."""

import logging
import uuid

from langchain_core.messages import HumanMessage

from backend.app.agent.graph import build_graph
from backend.app.agent.orchestrator.agent import ORCHESTRATOR_MAX_ITERATIONS
from backend.app.agent.orchestrator.callback import OrchestratorLogCallback
from backend.app.agent.orchestrator.context import (
    cleanup_analysis_context,
    init_analysis_context,
)
from backend.app.db.repositories import analysis_repo, deal_repo
from backend.app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


def _classify_error(exc: Exception) -> str:
    """Derive a user-friendly Korean error message from an exception."""
    exc_type = type(exc).__name__
    msg = str(exc).lower()

    if "pinecone" in msg or "pinecone" in exc_type.lower():
        return "벡터 DB(Pinecone) 연결에 실패했습니다. API 키를 확인해주세요."
    if "authentication" in msg or "authenticationerror" in exc_type.lower():
        return "LLM API 인증에 실패했습니다. API 키를 확인해주세요."
    if "ratelimit" in exc_type.lower() or "rate_limit" in msg or "rate limit" in msg:
        return "API 호출 한도를 초과했습니다. 잠시 후 다시 시도해주세요."
    if "timeout" in exc_type.lower() or "timeout" in msg:
        return "분석 시간이 초과되었습니다. 다시 시도해주세요."
    if "integrityerror" in exc_type.lower():
        return "데이터 충돌이 발생했습니다. 다시 시도해주세요."
    if "connection" in msg or "connect" in msg:
        return "외부 서비스 연결에 실패했습니다. 네트워크 상태를 확인해주세요."

    return f"분석 중 오류가 발생했습니다: {exc_type}"


class AnalysisService:
    """Run the full deal-analysis pipeline and persist results."""

    async def run_analysis(self, deal_id: uuid.UUID) -> None:
        """Execute the orchestrator pipeline for *deal_id* and save results.

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

                # Remove any previous analysis result to avoid unique constraint violation
                await analysis_repo.delete_by_deal_id(db, deal_id)
                await db.flush()

                deal_id_str = str(deal_id)

                # Progress callback — updates deal.current_step in DB
                async def on_progress(step_label: str) -> None:
                    deal.current_step = step_label
                    await db.commit()

                # Initialize per-deal analysis context
                ctx = init_analysis_context(
                    deal_id=deal_id_str,
                    deal_input=deal.raw_input or "",
                    on_progress=on_progress,
                )

                # Create orchestrator callback for hierarchical logging
                orch_callback = OrchestratorLogCallback(deal_id=deal_id)
                ctx.orchestrator_callback = orch_callback

                # Build and invoke orchestrator graph
                logger.info("Building orchestrator for deal %s", deal_id)
                graph = build_graph(deal_id=deal_id_str)

                user_message = (
                    f"Analyze the following deal for a Go/No-Go decision.\n\n"
                    f"Deal ID: {deal_id_str}\n\n"
                    f"Deal Input:\n{deal.raw_input or ''}"
                )

                logger.info("Starting orchestrator execution for deal %s", deal_id)
                await graph.ainvoke(
                    {"messages": [HumanMessage(content=user_message)]},
                    config={
                        "recursion_limit": 2 * ORCHESTRATOR_MAX_ITERATIONS + 1,
                        "callbacks": [orch_callback],
                    },
                )

                # Extract accumulated results from context
                result = cleanup_analysis_context(deal_id_str)
                if result is None:
                    raise RuntimeError("AnalysisContext was not found after orchestrator completion")

                # Persist analysis result
                await analysis_repo.create(
                    db,
                    deal_id=deal_id,
                    total_score=result.get("total_score"),
                    verdict=result.get("verdict"),
                    scores=result.get("scores"),
                    resource_estimate=result.get("resource_estimate"),
                    risks=result.get("risks"),
                    risk_interdependencies=result.get("risk_interdependencies"),
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

            except Exception as exc:
                logger.exception("Analysis failed for deal %s", deal_id)
                # Ensure context is cleaned up even on failure
                cleanup_analysis_context(str(deal_id))
                await db.rollback()
                error_msg = _classify_error(exc)
                # Mark deal as failed using a fresh session
                try:
                    async with AsyncSessionLocal() as err_db:
                        err_deal = await deal_repo.get_by_id(err_db, deal_id)
                        if err_deal is not None:
                            err_deal.current_step = None
                            err_deal.error_message = error_msg
                        await deal_repo.update_status(err_db, deal_id, "failed")
                        await err_db.commit()
                except Exception:
                    logger.exception("Failed to update deal %s status to 'failed'", deal_id)
