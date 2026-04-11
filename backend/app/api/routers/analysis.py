"""Analysis trigger, results, and status endpoints."""

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, BackgroundTasks, Body, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agent.service import AnalysisService, resolve_workflow_type
from backend.app.api.exceptions import (
    AnalysisInProgress,
    AnalysisNotFound,
    DealNotFound,
    OathKeeperError,
)
from backend.app.api.schemas.analysis import AnalysisResponse, AnalysisTriggerResponse
from backend.app.db.repositories import analysis_repo, deal_repo
from backend.app.db.session import get_db

router = APIRouter(prefix="/api/deals", tags=["analysis"])


@router.post(
    "/{deal_id}/analyze",
    response_model=AnalysisTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_analysis(
    deal_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    workflow_type: str | None = Body(None, embed=True),
) -> AnalysisTriggerResponse:
    deal = await deal_repo.get_by_id(db, deal_id)
    if deal is None:
        raise DealNotFound(deal_id)
    if deal.status == "analyzing":
        raise AnalysisInProgress(deal_id)
    if not (deal.raw_input or "").strip():
        raise OathKeeperError(
            "분석할 Deal 정보가 없습니다. Notion 내용 또는 추가 정보를 입력해���세요.",
            status_code=422,
        )

    # Resolve workflow type: explicit request > system setting > default
    resolved_wf = await resolve_workflow_type(workflow_type, db=db)

    await deal_repo.update_status(db, deal_id, "analyzing")
    deal.current_step = "Deal 구조화 준비 중..."
    deal.error_message = None
    await db.commit()

    service = AnalysisService()
    background_tasks.add_task(service.run_analysis, deal_id, resolved_wf)

    return AnalysisTriggerResponse(
        deal_id=deal_id,
        status="analyzing",
        message=f"Analysis started (workflow: {resolved_wf.value})",
    )


@router.get("/{deal_id}/analysis", response_model=AnalysisResponse)
async def get_analysis(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> AnalysisResponse:
    deal = await deal_repo.get_by_id(db, deal_id)
    if deal is None:
        raise DealNotFound(deal_id)

    analysis = await analysis_repo.get_by_deal_id(db, deal_id)
    if analysis is None:
        raise AnalysisNotFound(deal_id)
    return AnalysisResponse.model_validate(analysis)


@router.get("/{deal_id}/status")
async def get_analysis_status(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    deal = await deal_repo.get_by_id(db, deal_id)
    if deal is None:
        raise DealNotFound(deal_id)

    async def event_stream() -> AsyncGenerator[str, None]:
        last_payload: str | None = None
        for _ in range(600):  # max ~150 seconds
            from backend.app.db.session import AsyncSessionLocal

            async with AsyncSessionLocal() as poll_db:
                poll_deal = await deal_repo.get_by_id(poll_db, deal_id)
                if poll_deal is None:
                    break
                payload = json.dumps(
                    {
                        "deal_id": str(deal_id),
                        "status": poll_deal.status,
                        "current_step": poll_deal.current_step,
                    },
                )
                if payload != last_payload:
                    yield f"data: {payload}\n\n"
                    last_payload = payload
                if poll_deal.status in ("completed", "failed"):
                    break
            await asyncio.sleep(0.25)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
