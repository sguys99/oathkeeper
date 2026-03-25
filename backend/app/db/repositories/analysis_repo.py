"""Analysis result repository — CRUD operations for the analysis_results table."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.analysis_result import AnalysisResult


async def create(
    session: AsyncSession,
    *,
    deal_id: uuid.UUID,
    total_score: float | None = None,
    verdict: str | None = None,
    scores: dict | None = None,
    resource_estimate: dict | None = None,
    risks: dict | None = None,
    risk_interdependencies: dict | None = None,
    similar_projects: dict | None = None,
    report_markdown: str | None = None,
) -> AnalysisResult:
    analysis = AnalysisResult(
        id=uuid.uuid4(),
        deal_id=deal_id,
        total_score=total_score,
        verdict=verdict,
        scores=scores,
        resource_estimate=resource_estimate,
        risks=risks,
        risk_interdependencies=risk_interdependencies,
        similar_projects=similar_projects,
        report_markdown=report_markdown,
    )
    session.add(analysis)
    await session.flush()
    return analysis


async def delete_by_deal_id(session: AsyncSession, deal_id: uuid.UUID) -> None:
    """Delete existing analysis result for a deal (if any) to allow re-analysis."""
    result = await session.execute(select(AnalysisResult).where(AnalysisResult.deal_id == deal_id))
    existing = result.scalar_one_or_none()
    if existing is not None:
        await session.delete(existing)
        await session.flush()


async def get_by_deal_id(session: AsyncSession, deal_id: uuid.UUID) -> AnalysisResult | None:
    result = await session.execute(select(AnalysisResult).where(AnalysisResult.deal_id == deal_id))
    return result.scalar_one_or_none()


async def update_notion_saved(
    session: AsyncSession,
    analysis_id: uuid.UUID,
    saved_at: datetime,
) -> AnalysisResult | None:
    analysis = await session.get(AnalysisResult, analysis_id)
    if analysis is None:
        return None
    analysis.notion_saved_at = saved_at
    await session.flush()
    return analysis
