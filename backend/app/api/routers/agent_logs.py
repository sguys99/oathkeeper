"""Agent log endpoints — view per-node LLM execution logs."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.exceptions import DealNotFound
from backend.app.api.schemas.agent_log import AgentLogResponse
from backend.app.db.repositories import agent_log_repo, deal_repo
from backend.app.db.session import get_db

router = APIRouter(prefix="/api/deals", tags=["agent-logs"])


@router.get("/{deal_id}/logs", response_model=list[AgentLogResponse])
async def get_agent_logs(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[AgentLogResponse]:
    deal = await deal_repo.get_by_id(db, deal_id)
    if deal is None:
        raise DealNotFound(deal_id)

    logs = await agent_log_repo.list_by_deal_id(db, deal_id)
    return [AgentLogResponse.model_validate(log) for log in logs]
