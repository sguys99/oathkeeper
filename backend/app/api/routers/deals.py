"""Deal management endpoints."""

import logging
import uuid

from fastapi import APIRouter, Depends, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.exceptions import (
    DealNotFound,
    DuplicateNotionDeal,
    OathKeeperError,
)
from backend.app.api.schemas.deal import (
    DealCreate,
    DealListResponse,
    DealResponse,
    DealStatus,
)
from backend.app.db.models.deal import Deal
from backend.app.db.repositories import deal_repo
from backend.app.db.session import get_db
from backend.app.integrations import notion_service
from backend.app.utils.file_parser import FileParseError, UnsupportedFileType, extract_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/deals", tags=["deals"])


@router.post("/", response_model=DealResponse, status_code=status.HTTP_201_CREATED)
async def create_deal(
    body: DealCreate,
    db: AsyncSession = Depends(get_db),
) -> DealResponse:
    if body.notion_page_id:
        existing = await deal_repo.get_by_notion_page_id(db, body.notion_page_id)
        if existing:
            raise DuplicateNotionDeal(existing.id)

    # Build raw_input: Notion page content + user's additional info
    raw_input_parts: list[str] = []
    if body.notion_page_id:
        try:
            notion_content = await notion_service.get_deal_content(body.notion_page_id)
            if notion_content:
                raw_input_parts.append(notion_content)
        except Exception:
            logger.warning("Failed to fetch Notion page content for %s", body.notion_page_id)
    if body.raw_input:
        raw_input_parts.append(body.raw_input)

    combined_raw_input = "\n\n---\n\n".join(raw_input_parts) if raw_input_parts else None

    deal = await deal_repo.create(
        db,
        title=body.title,
        raw_input=combined_raw_input,
        notion_page_id=body.notion_page_id,
        created_by=body.created_by,
    )
    return DealResponse.model_validate(deal)


@router.get("/", response_model=DealListResponse)
async def list_deals(
    db: AsyncSession = Depends(get_db),
    status: DealStatus | None = None,
    created_by: uuid.UUID | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> DealListResponse:
    status_value = status.value if status is not None else None
    items = await deal_repo.list_with_filters(
        db,
        status=status_value,
        created_by=created_by,
        offset=offset,
        limit=limit,
    )
    return DealListResponse(
        items=[DealResponse.model_validate(d) for d in items],
        total=len(items),
        offset=offset,
        limit=limit,
    )


@router.get("/notion-page-ids", response_model=list[str])
async def list_imported_notion_page_ids(
    db: AsyncSession = Depends(get_db),
) -> list[str]:
    """Return all notion_page_id values that already have deals."""
    stmt = select(Deal.notion_page_id).where(Deal.notion_page_id.isnot(None))
    result = await db.execute(stmt)
    return [row[0] for row in result.all()]


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> DealResponse:
    deal = await deal_repo.get_by_id(db, deal_id)
    if deal is None:
        raise DealNotFound(deal_id)
    return DealResponse.model_validate(deal)


_MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB


@router.post("/{deal_id}/upload", response_model=DealResponse)
async def upload_deal_document(
    deal_id: uuid.UUID,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
) -> DealResponse:
    """Upload a Word (.docx) or PDF file and append extracted text to the deal."""
    deal = await deal_repo.get_by_id(db, deal_id)
    if deal is None:
        raise DealNotFound(deal_id)

    content = await file.read()

    if len(content) > _MAX_UPLOAD_BYTES:
        raise OathKeeperError("File too large (max 20MB)", status_code=413)

    try:
        extracted = extract_text(file.filename or "unknown", content)
    except UnsupportedFileType as e:
        raise OathKeeperError(
            "Unsupported file type. Only .docx and .pdf are accepted.",
            status_code=415,
        ) from e
    except FileParseError as e:
        raise OathKeeperError(str(e), status_code=422) from e

    # Append extracted text to raw_input
    existing = deal.raw_input or ""
    separator = "\n\n---\n\n" if existing else ""
    deal.raw_input = existing + separator + extracted
    await db.commit()

    return DealResponse.model_validate(deal)


@router.delete("/{deal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deal(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a deal and its analysis result. Archives the Notion page if linked."""
    deal = await deal_repo.get_by_id(db, deal_id)
    if deal is None:
        raise DealNotFound(deal_id)
    # Best-effort: archive ai decision pages linked to this deal
    if deal.notion_page_id:
        await notion_service.archive_decision_pages(deal.notion_page_id)

    await deal_repo.delete(db, deal_id)
