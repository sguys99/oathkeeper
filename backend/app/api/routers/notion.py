"""Notion integration endpoints — deal listing and analysis save."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.exceptions import AnalysisNotFound, DealNotFound, NotionAPIError
from backend.app.api.schemas.notion import NotionDealListResponse, NotionSaveRequest, NotionSaveResponse
from backend.app.db.repositories import analysis_repo, deal_repo
from backend.app.db.session import get_db
from backend.app.integrations import notion_service, slack_client

router = APIRouter(prefix="/api", tags=["notion"])


@router.get("/notion/deals", response_model=NotionDealListResponse)
async def list_notion_deals(
    db: AsyncSession = Depends(get_db),
) -> NotionDealListResponse:
    """Fetch deals from the Notion deal information database."""
    try:
        deals = await notion_service.list_deals()
    except Exception as e:
        raise NotionAPIError(detail=str(e)) from e
    return NotionDealListResponse(deals=deals)


@router.post("/deals/{deal_id}/save-to-notion", response_model=NotionSaveResponse)
async def save_to_notion(
    deal_id: uuid.UUID,
    body: NotionSaveRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> NotionSaveResponse:
    """Save analysis results to the Notion ai decision database."""
    # 1. Load analysis result
    analysis = await analysis_repo.get_by_deal_id(db, deal_id)
    if analysis is None:
        raise AnalysisNotFound(deal_id)

    # 2. Load deal for notion_page_id and title
    deal = await deal_repo.get_by_id(db, deal_id)
    if deal is None:
        raise DealNotFound(deal_id)

    # 3. Save to Notion
    try:
        result = await notion_service.save_analysis_to_notion(
            analysis=analysis,
            deal_page_id=deal.notion_page_id,
        )
    except Exception as e:
        raise NotionAPIError(detail=str(e)) from e

    # 4. Update notion_saved_at in DB
    if result.saved_at:
        await analysis_repo.update_notion_saved(db, analysis.id, result.saved_at)
        await db.commit()

    # 5. Send Slack notification (fire-and-forget)
    await slack_client.send_analysis_notification(
        deal_name=deal.title,
        verdict=analysis.verdict or "unknown",
        total_score=float(analysis.total_score or 0),
        notion_page_url=result.notion_page_url,
    )

    return result
