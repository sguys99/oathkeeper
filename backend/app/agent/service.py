"""Analysis service — orchestrates workflow execution and DB persistence."""

import logging
import uuid

from backend.app.agent.workflows import WorkflowType, get_workflow
from backend.app.db.repositories import analysis_repo, deal_repo, settings_repo
from backend.app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

DEFAULT_WORKFLOW_TYPE = WorkflowType.STATIC


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
    if "invalidrequesterror" in exc_type.lower() or "concurrent" in msg:
        return "내부 데이터베이스 세션 오류가 발생했습니다. 다시 시도해주세요."
    if "connection" in msg or "connect" in msg:
        return "외부 서비스 연결에 실패했습니다. 네트워크 상태를 확인해주세요."

    return f"분석 중 오류가 발생했습니다: {exc_type}"


async def resolve_workflow_type(
    requested: str | None,
    db=None,
) -> WorkflowType:
    """Resolve workflow type from request or system default.

    Priority: explicit request > company setting > DEFAULT_WORKFLOW_TYPE.
    """
    if requested:
        try:
            return WorkflowType(requested)
        except ValueError:
            logger.warning("Invalid workflow_type '%s', falling back to default", requested)

    # Check company settings for default
    try:
        if db is not None:
            setting = await settings_repo.get_setting(db, "default_workflow_type")
            if setting and setting.value:
                return WorkflowType(setting.value)
        else:
            async with AsyncSessionLocal() as session:
                setting = await settings_repo.get_setting(session, "default_workflow_type")
                if setting and setting.value:
                    return WorkflowType(setting.value)
    except (ValueError, Exception):
        logger.debug("Could not read default_workflow_type from settings, using fallback")

    return DEFAULT_WORKFLOW_TYPE


class AnalysisService:
    """Run the full deal-analysis pipeline and persist results."""

    async def run_analysis(
        self,
        deal_id: uuid.UUID,
        workflow_type: WorkflowType = DEFAULT_WORKFLOW_TYPE,
    ) -> None:
        """Execute the analysis pipeline for *deal_id* and save results.

        Creates its own DB session because this method runs inside
        ``BackgroundTasks`` (outside the request lifecycle).
        """
        logger.info(
            "run_analysis started for deal %s (workflow=%s)",
            deal_id,
            workflow_type,
        )
        async with AsyncSessionLocal() as db:
            try:
                deal = await deal_repo.get_by_id(db, deal_id)
                if deal is None:
                    logger.error("Deal %s not found — skipping analysis", deal_id)
                    return

                # Remove any previous analysis result to avoid unique constraint violation
                await analysis_repo.delete_by_deal_id(db, deal_id)
                await db.flush()

                # Progress callback — uses its own session to avoid
                # concurrent-commit errors when workers run in parallel.
                async def on_progress(step_label: str) -> None:
                    async with AsyncSessionLocal() as progress_db:
                        progress_deal = await deal_repo.get_by_id(progress_db, deal_id)
                        if progress_deal is not None:
                            progress_deal.current_step = step_label
                            await progress_db.commit()

                # Execute the selected workflow
                workflow = get_workflow(workflow_type)
                result = await workflow.execute(
                    deal_id=deal_id,
                    deal_input=deal.raw_input or "",
                    on_progress=on_progress,
                )

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
                    workflow_type=workflow_type.value,
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
