import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from backend.app.api.schemas.base import OrmBase

# --- Scoring Criteria ---


class ScoringCriteriaResponse(OrmBase):
    id: uuid.UUID
    name: str
    weight: float
    description: str | None = None
    is_active: bool
    display_order: int
    updated_at: datetime


class WeightUpdateItem(BaseModel):
    id: uuid.UUID
    weight: float = Field(ge=0, le=1)


class WeightUpdateRequest(BaseModel):
    weights: list[WeightUpdateItem]

    @model_validator(mode="after")
    def check_weight_sum(self) -> "WeightUpdateRequest":
        total = sum(w.weight for w in self.weights)
        if abs(total - 1.0) > 0.001:
            msg = f"Weights must sum to 1.0 (got {total:.4f})"
            raise ValueError(msg)
        return self


# --- Company Settings ---


class CompanySettingResponse(OrmBase):
    key: str
    value: str
    description: str | None = None
    updated_at: datetime


class CompanySettingUpsert(BaseModel):
    key: str
    value: str
    description: str | None = None


# --- Team Members ---


class TeamMemberCreate(BaseModel):
    name: str
    role: Literal["PM", "FE", "BE", "MLE", "DevOps"]
    monthly_rate: int = Field(gt=0)
    is_available: bool = True
    current_project: str | None = None
    available_from: date | None = None


class TeamMemberUpdate(BaseModel):
    name: str | None = None
    role: Literal["PM", "FE", "BE", "MLE", "DevOps"] | None = None
    monthly_rate: int | None = Field(default=None, gt=0)
    is_available: bool | None = None
    current_project: str | None = None
    available_from: date | None = None


class TeamMemberResponse(OrmBase):
    id: uuid.UUID
    name: str
    role: str
    monthly_rate: int
    is_available: bool
    current_project: str | None = None
    available_from: date | None = None
    created_at: datetime
    updated_at: datetime
