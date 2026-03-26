import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, model_validator

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
    verdict: str | None = None
    total_score: float | None = None

    @model_validator(mode="before")
    @classmethod
    def _extract_analysis_fields(cls, data: object) -> object:
        """Pull verdict and total_score from the related AnalysisResult."""
        try:
            ar = data.analysis_result  # type: ignore[union-attr]
            if ar is not None:
                data.verdict = ar.verdict  # type: ignore[union-attr]
                data.total_score = ar.total_score  # type: ignore[union-attr]
        except Exception:
            pass
        return data


class DealListResponse(BaseModel):
    items: list[DealResponse]
    total: int
    offset: int
    limit: int
