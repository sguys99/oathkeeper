import uuid
from datetime import datetime
from typing import Any

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
