"""Agent log endpoints — view per-node LLM execution logs."""

import uuid
from enum import StrEnum

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.exceptions import DealNotFound
from backend.app.api.schemas.agent_log import (
    AgentLogResponse,
    AgentLogTreeNode,
    AgentLogTreeResponse,
)
from backend.app.db.repositories import agent_log_repo, deal_repo
from backend.app.db.session import get_db

router = APIRouter(prefix="/api/deals", tags=["agent-logs"])


class LogView(StrEnum):
    FLAT = "flat"
    TREE = "tree"


def _build_tree_node(log) -> AgentLogTreeNode:
    """Recursively build a tree node from an AgentLog ORM object."""
    children = [_build_tree_node(child) for child in (log.children or [])]
    node_data = AgentLogResponse.model_validate(log).model_dump()
    return AgentLogTreeNode(**node_data, children=children)


@router.get("/{deal_id}/logs")
async def get_agent_logs(
    deal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    view: LogView = Query(LogView.FLAT),
    step_type: str | None = Query(None),
    worker_name: str | None = Query(None),
) -> list[AgentLogResponse] | AgentLogTreeResponse:
    deal = await deal_repo.get_by_id(db, deal_id)
    if deal is None:
        raise DealNotFound(deal_id)

    if view == LogView.TREE:
        all_logs = await agent_log_repo.list_by_deal_id_with_children(db, deal_id)
        root_logs = [log for log in all_logs if log.parent_log_id is None]
        tree_nodes = [_build_tree_node(log) for log in root_logs]

        total_duration = sum(log.duration_ms or 0 for log in all_logs)
        return AgentLogTreeResponse(
            deal_id=deal_id,
            logs=tree_nodes,
            total_count=len(all_logs),
            total_duration_ms=total_duration,
        )

    # Flat view with optional filters
    logs = await agent_log_repo.list_by_deal_id(db, deal_id)
    result = [AgentLogResponse.model_validate(log) for log in logs]
    if step_type:
        result = [r for r in result if r.step_type == step_type]
    if worker_name:
        result = [r for r in result if r.worker_name == worker_name]
    return result
