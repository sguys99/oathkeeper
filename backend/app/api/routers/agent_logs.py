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
    flat = "flat"
    tree = "tree"


def _build_tree_node(log) -> AgentLogTreeNode:
    """Recursively build a tree node from an ORM object with children."""
    node = AgentLogTreeNode.model_validate(log)
    children = sorted(
        log.children or [],
        key=lambda child: (
            child.started_at,
            child.step_index if child.step_index is not None else -1,
        ),
    )
    node.children = [_build_tree_node(child) for child in children]
    return node


@router.get("/{deal_id}/logs")
async def get_agent_logs(
    deal_id: uuid.UUID,
    view: LogView = Query(LogView.flat, description="flat or tree"),
    step_type: str | None = Query(None, description="Filter by step_type"),
    worker_name: str | None = Query(None, description="Filter by worker_name"),
    db: AsyncSession = Depends(get_db),
) -> list[AgentLogResponse] | AgentLogTreeResponse:
    deal = await deal_repo.get_by_id(db, deal_id)
    if deal is None:
        raise DealNotFound(deal_id)

    if view == LogView.tree:
        logs = await agent_log_repo.list_by_deal_id_with_children(db, deal_id)
        root_logs = [log for log in logs if log.parent_log_id is None]
        return AgentLogTreeResponse(
            deal_id=deal_id,
            logs=[_build_tree_node(log) for log in root_logs],
            total_count=len(logs),
            total_duration_ms=sum(log.duration_ms or 0 for log in logs),
        )

    # Default flat view (backward compatible)
    logs = await agent_log_repo.list_by_deal_id(db, deal_id)
    if step_type:
        logs = [log for log in logs if log.step_type == step_type]
    if worker_name:
        logs = [log for log in logs if log.worker_name == worker_name]
    return [AgentLogResponse.model_validate(log) for log in logs]
