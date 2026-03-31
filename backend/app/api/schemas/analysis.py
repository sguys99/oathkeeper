import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel

from backend.app.api.schemas.base import OrmBase


class VerdictEnum(StrEnum):
    go = "go"
    conditional_go = "conditional_go"
    no_go = "no_go"
    pending = "pending"


class ScoreDetail(BaseModel):
    criterion: str
    score: float
    weight: float
    weighted_score: float
    rationale: str | None = None


class ResourceEstimate(BaseModel):
    team_composition: list[dict[str, Any]] | None = None
    duration_months: float | None = None
    total_cost: int | None = None
    expected_margin: float | None = None
    rationale: str | None = None


class RiskItem(BaseModel):
    category: str
    item: str
    probability: str | None = None  # HIGH, MEDIUM, LOW
    impact: str | None = None  # HIGH, MEDIUM, LOW
    level: str  # HIGH, MEDIUM, LOW (derived from probability × impact matrix)
    evidence: str | None = None
    description: str
    mitigation: str | None = None


class RiskInterdependency(BaseModel):
    risk_pair: list[str]
    combined_effect: str
    amplification: str


class SimilarProject(BaseModel):
    project_name: str
    similarity_score: float
    industry: str | None = None
    tech_stack: list[str] | None = None
    duration_months: float | None = None
    result: str | None = None
    lessons_learned: str | None = None


class AnalysisResponse(OrmBase):
    id: uuid.UUID
    deal_id: uuid.UUID
    total_score: float | None = None
    verdict: str | None = None
    scores: Any | None = None
    resource_estimate: Any | None = None
    risks: Any | None = None
    risk_interdependencies: Any | None = None
    similar_projects: Any | None = None
    report_markdown: str | None = None
    notion_saved_at: datetime | None = None
    created_at: datetime


class AnalysisTriggerResponse(BaseModel):
    deal_id: uuid.UUID
    status: str
    message: str


class AnalysisStatusEvent(BaseModel):
    deal_id: uuid.UUID
    status: str
    current_step: str | None = None
    updated_at: datetime
