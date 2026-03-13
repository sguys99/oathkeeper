"""Analysis trigger, results, and status endpoints."""

import json
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agent.service import AnalysisService
from backend.app.api.exceptions import AnalysisInProgress, AnalysisNotFound, DealNotFound
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
) -> AnalysisTriggerResponse:
    deal = await deal_repo.get_by_id(db, deal_id)
    if deal is None:
        raise DealNotFound(deal_id)
    if deal.status == "analyzing":
        raise AnalysisInProgress(deal_id)

    await deal_repo.update_status(db, deal_id, "analyzing")
    deal.current_step = "Deal 구조화 준비 중..."
    await db.commit()

    service = AnalysisService()
    background_tasks.add_task(service.run_analysis, deal_id)

    return AnalysisTriggerResponse(
        deal_id=deal_id,
        status="analyzing",
        message="Analysis started",
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
        data = json.dumps({"deal_id": str(deal_id), "status": deal.status})
        yield f"data: {data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
