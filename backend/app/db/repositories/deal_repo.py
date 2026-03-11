"""Deal repository — CRUD operations for the deals table."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.deal import Deal


async def create(
    session: AsyncSession,
    *,
    title: str,
    raw_input: str | None = None,
    notion_page_id: str | None = None,
    structured_data: dict | None = None,
    created_by: uuid.UUID | None = None,
) -> Deal:
    deal = Deal(
        id=uuid.uuid4(),
        title=title,
        raw_input=raw_input,
        notion_page_id=notion_page_id,
        structured_data=structured_data,
        created_by=created_by,
    )
    session.add(deal)
    await session.flush()
    return deal


async def get_by_id(session: AsyncSession, deal_id: uuid.UUID) -> Deal | None:
    return await session.get(Deal, deal_id)


async def list_with_filters(
    session: AsyncSession,
    *,
    status: str | None = None,
    created_by: uuid.UUID | None = None,
    offset: int = 0,
    limit: int = 20,
) -> list[Deal]:
    stmt = select(Deal).order_by(Deal.created_at.desc())
    if status is not None:
        stmt = stmt.where(Deal.status == status)
    if created_by is not None:
        stmt = stmt.where(Deal.created_by == created_by)
    stmt = stmt.offset(offset).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_status(session: AsyncSession, deal_id: uuid.UUID, status: str) -> Deal | None:
    deal = await session.get(Deal, deal_id)
    if deal is None:
        return None
    deal.status = status
    await session.flush()
    return deal
