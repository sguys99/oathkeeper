"""Analysis trigger, results, and status endpoints."""

import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC

from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agent.service import AnalysisService
from backend.app.api.exceptions import (
    AnalysisInProgress,
    AnalysisNotFound,
    DealNotFound,
    OathKeeperError,
)
from backend.app.api.schemas.analysis import (
    AnalysisResponse,
    AnalysisStatusEvent,
    AnalysisTriggerResponse,
)
from backend.app.db.repositories import analysis_repo, deal_repo
from backend.app.db.session import AsyncSessionLocal, get_db

router = APIRouter(prefix="/api/deals", tags=["analysis"])
STATUS_STREAM_POLL_INTERVAL_SECONDS = 0.25


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
    if not (deal.raw_input or "").strip():
        raise OathKeeperError(
            "분석할 Deal 정보가 없습니다. Notion 내용 또는 추가 정보를 입력해주세요.",
            status_code=422,
        )

    await deal_repo.update_status(db, deal_id, "analyzing")
    deal.current_step = "Deal 구조화 준비 중..."
    deal.error_message = None
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

    async def build_event_payload() -> str | None:
        async with AsyncSessionLocal() as session:
            refreshed = await deal_repo.get_by_id(session, deal_id)
            if refreshed is None:
                return None

            event = AnalysisStatusEvent(
                deal_id=deal_id,
                status=refreshed.status,
                current_step=refreshed.current_step,
                updated_at=refreshed.updated_at
                if refreshed.updated_at.tzinfo is not None
                else refreshed.updated_at.replace(tzinfo=UTC),
            )
            return event.model_dump_json()

    async def event_stream() -> AsyncGenerator[str, None]:
        last_payload: str | None = None

        while True:
            payload = await build_event_payload()
            if payload is None:
                return

            if payload != last_payload:
                yield f"data: {payload}\n\n"
                event = json.loads(payload)
                last_payload = payload
                if event["status"] in {"completed", "failed"}:
                    return

            await asyncio.sleep(STATUS_STREAM_POLL_INTERVAL_SECONDS)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
