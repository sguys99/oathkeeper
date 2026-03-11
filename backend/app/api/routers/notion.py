"""Notion integration endpoints (stubs for Phase 6)."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.exceptions import NotionAPIError
from backend.app.api.schemas.notion import NotionDealListResponse, NotionSaveRequest, NotionSaveResponse
from backend.app.db.session import get_db

router = APIRouter(prefix="/api", tags=["notion"])


@router.get("/notion/deals", response_model=NotionDealListResponse)
async def list_notion_deals(
    db: AsyncSession = Depends(get_db),
) -> NotionDealListResponse:
    raise NotionAPIError("Notion integration not yet implemented (Phase 6)")


@router.post("/deals/{deal_id}/save-to-notion", response_model=NotionSaveResponse)
async def save_to_notion(
    deal_id: uuid.UUID,
    body: NotionSaveRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> NotionSaveResponse:
    raise NotionAPIError("Notion integration not yet implemented (Phase 6)")
