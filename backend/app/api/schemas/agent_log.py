import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from backend.app.api.schemas.base import OrmBase


class AgentLogResponse(OrmBase):
    id: uuid.UUID
    deal_id: uuid.UUID
    node_name: str
    system_prompt: str | None = None
    user_prompt: str | None = None
    raw_output: str | None = None
    parsed_output: Any | None = None
    error: str | None = None
    duration_ms: int | None = None
    started_at: datetime
    completed_at: datetime | None = None
    created_at: datetime
    # Hierarchical fields
    parent_log_id: uuid.UUID | None = None
    step_type: str | None = None
    step_index: int | None = None
    tool_name: str | None = None
    worker_name: str | None = None


class AgentLogTreeNode(AgentLogResponse):
    children: list["AgentLogTreeNode"] = []


class AgentLogTreeResponse(BaseModel):
    deal_id: uuid.UUID
    logs: list[AgentLogTreeNode]
    total_count: int
    total_duration_ms: int
