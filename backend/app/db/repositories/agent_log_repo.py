"""Agent log repository — CRUD operations for the agent_logs table."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.agent_log import AgentLog


async def create(
    session: AsyncSession,
    *,
    deal_id: uuid.UUID,
    node_name: str,
    system_prompt: str | None = None,
    user_prompt: str | None = None,
    raw_output: str | None = None,
    parsed_output: dict | None = None,
    error: str | None = None,
    duration_ms: int | None = None,
    started_at: datetime,
    completed_at: datetime | None = None,
) -> AgentLog:
    log = AgentLog(
        id=uuid.uuid4(),
        deal_id=deal_id,
        node_name=node_name,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        raw_output=raw_output,
        parsed_output=parsed_output,
        error=error,
        duration_ms=duration_ms,
        started_at=started_at,
        completed_at=completed_at,
    )
    session.add(log)
    await session.flush()
    return log


async def list_by_deal_id(session: AsyncSession, deal_id: uuid.UUID) -> list[AgentLog]:
    result = await session.execute(
        select(AgentLog).where(AgentLog.deal_id == deal_id).order_by(AgentLog.started_at),
    )
    return list(result.scalars().all())


async def update_parsed_output(
    session: AsyncSession,
    log_id: uuid.UUID,
    parsed_output: dict | None,
) -> AgentLog | None:
    log = await session.get(AgentLog, log_id)
    if log is None:
        return None
    log.parsed_output = parsed_output
    await session.flush()
    return log
