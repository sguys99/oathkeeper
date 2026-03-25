import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel

from backend.app.api.schemas.base import OrmBase
from backend.app.api.schemas.user import UserResponse


class DealStatus(StrEnum):
    pending = "pending"
    analyzing = "analyzing"
    completed = "completed"
    failed = "failed"


class DealCreate(BaseModel):
    title: str
    raw_input: str | None = None
    notion_page_id: str | None = None
    created_by: uuid.UUID | None = None


class DealResponse(OrmBase):
    id: uuid.UUID
    notion_page_id: str | None = None
    title: str
    raw_input: str | None = None
    structured_data: dict | None = None
    status: DealStatus
    current_step: str | None = None
    error_message: str | None = None
    created_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime
    creator: UserResponse | None = None


class DealListResponse(BaseModel):
    items: list[DealResponse]
    total: int
    offset: int
    limit: int
