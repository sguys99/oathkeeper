"""Meta-tools — orchestrator-level tools that invoke analysis workers."""

from __future__ import annotations

import json
import logging
import uuid

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from backend.app.agent.base import CRITICAL_FIELDS, MISSING_FIELDS_THRESHOLD
from backend.app.agent.orchestrator.context import get_analysis_context

logger = logging.getLogger(__name__)


def _get_parent_log_id(deal_id: str, tool_name: str | None = None) -> uuid.UUID | None:
    """Extract parent_log_id from the orchestrator callback, if available.

    When *tool_name* is given, uses the parallel-safe per-name lookup so that
    each meta-tool gets its own ``orchestrator_tool_call`` log as parent.
    Falls back to ``last_tool_call_log_id`` for backward compatibility.
    """
    ctx = get_analysis_context(deal_id)
    cb = ctx.orchestrator_callback
    if cb is None:
        return None
    if tool_name:
        log_id = cb.get_tool_call_log_id(tool_name)
        if log_id:
            return log_id
    return cb.last_tool_call_log_id


STEP_LABELS: dict[str, str] = {
    "deal_structuring": "Deal 구조화 중...",
    "scoring": "평가 기준 분석 중...",
    "resource_estimation": "리소스 추정 중...",
    "risk_analysis": "리스크 분석 중...",
    "similar_project": "유사 프로젝트 검색 중...",
    "final_verdict": "최종 판정 중...",
}


async def _report_progress(deal_id: str, worker_name: str) -> None:
    """Fire progress callback if registered."""
    ctx = get_analysis_context(deal_id)
    label = STEP_LABELS.get(worker_name)
    if label and ctx.on_progress:
        await ctx.on_progress(label)


# -- Pydantic schemas for meta-tools ----------------------------------


class DealIdInput(BaseModel):
    deal_id: str = Field(description="The deal UUID string.")


class FinalVerdictInput(BaseModel):
    deal_id: str = Field(description="The deal UUID string.")
    hold: bool = Field(
        default=False,
        description="If true, generate a hold verdict (missing critical fields).",
    )


class CompanyContextInput(BaseModel):
    query: str = Field(description="Search query for company context.")


# -- Meta-tools --------------------------------------------------------


@tool(args_schema=DealIdInput)
async def run_deal_structuring(deal_id: str) -> str:
    """Extract structured fields from raw deal input.
    Must be called first. Returns structured deal data and hold recommendation."""
    from backend.app.agent.workers.deal_structuring import make_deal_structuring_worker_node

    ctx = get_analysis_context(deal_id)
    await _report_progress(deal_id, "deal_structuring")

    node_fn = make_deal_structuring_worker_node(
        parent_log_id=_get_parent_log_id(deal_id, "run_deal_structuring"),
    )
    result = await node_fn(ctx.to_agent_state())

    ctx.structured_deal = result.get("structured_deal", {})
    if result.get("errors"):
        ctx.errors.extend(result["errors"])

    # Check hold condition
    missing = [f for f in ctx.structured_deal.get("missing_fields", []) if f in CRITICAL_FIELDS]
    hold_recommended = len(missing) >= MISSING_FIELDS_THRESHOLD

    summary = {
        "status": "completed",
        "customer_name": ctx.structured_deal.get("customer_name", "unknown"),
        "project_overview": str(ctx.structured_deal.get("project_overview", ""))[:200],
        "missing_critical_fields": missing,
        "hold_recommended": hold_recommended,
    }

    if hold_recommended:
        return (
            f"HOLD_RECOMMENDED: {len(missing)} critical fields missing: "
            f"{', '.join(missing)}. Do NOT run analysis workers. "
            f"Call run_final_verdict with hold=true.\n\n"
            f"Structured deal summary: {json.dumps(summary, ensure_ascii=False)}"
        )

    return f"Deal structured successfully.\nSummary: {json.dumps(summary, ensure_ascii=False)}"


@tool(args_schema=DealIdInput)
async def run_scoring_analysis(deal_id: str) -> str:
    """Score the deal against 7 weighted evaluation criteria.
    Requires deal_structuring to have been completed first."""
    try:
        from backend.app.agent.workers.scoring import make_scoring_worker_node

        ctx = get_analysis_context(deal_id)
        await _report_progress(deal_id, "scoring")

        node_fn = make_scoring_worker_node(
            parent_log_id=_get_parent_log_id(deal_id, "run_scoring_analysis"),
        )
        result = await node_fn(ctx.to_agent_state())

        ctx.scores = result.get("scores", [])
        ctx.total_score = result.get("total_score", 0.0)
        ctx.verdict = result.get("verdict", "pending")
        if result.get("errors"):
            ctx.errors.extend(result["errors"])

        score_summary = [{s.get("criterion", "?"): s.get("weighted_score", 0)} for s in ctx.scores]
        return (
            f"Scoring complete. Total score: {ctx.total_score:.1f}, "
            f"Verdict: {ctx.verdict}. "
            f"Criteria scores: {json.dumps(score_summary, ensure_ascii=False)}"
        )
    except Exception as exc:
        logger.exception("run_scoring_analysis failed for deal %s", deal_id)
        ctx = get_analysis_context(deal_id)
        ctx.errors.append(f"scoring: {exc}")
        return f"ERROR: Scoring analysis failed: {exc}. Proceed with other results."


@tool(args_schema=DealIdInput)
async def run_resource_estimation(deal_id: str) -> str:
    """Estimate team composition, timeline, cost, and profitability.
    Requires deal_structuring to have been completed first."""
    try:
        from backend.app.agent.workers.resource_estimation import (
            make_resource_estimation_worker_node,
        )

        ctx = get_analysis_context(deal_id)
        await _report_progress(deal_id, "resource_estimation")

        node_fn = make_resource_estimation_worker_node(
            parent_log_id=_get_parent_log_id(deal_id, "run_resource_estimation"),
        )
        result = await node_fn(ctx.to_agent_state())

        ctx.resource_estimate = result.get("resource_estimate", {})
        if result.get("errors"):
            ctx.errors.extend(result["errors"])

        prof = ctx.resource_estimate.get("profitability", {})
        team = ctx.resource_estimate.get("team_composition", [])
        cost = ctx.resource_estimate.get("cost_breakdown", {})
        return (
            f"Resource estimation complete. "
            f"Expected margin: {prof.get('expected_margin', 'N/A')}%, "
            f"Team size: {len(team)} members, "
            f"Total cost: {cost.get('total_cost', 'N/A')}"
        )
    except Exception as exc:
        logger.exception("run_resource_estimation failed for deal %s", deal_id)
        ctx = get_analysis_context(deal_id)
        ctx.errors.append(f"resource_estimation: {exc}")
        return f"ERROR: Resource estimation failed: {exc}. Proceed with other results."


@tool(args_schema=DealIdInput)
async def run_risk_analysis(deal_id: str) -> str:
    """Identify and assess risks across 5 categories.
    Requires deal_structuring to have been completed first."""
    try:
        from backend.app.agent.workers.risk_analysis import make_risk_analysis_worker_node

        ctx = get_analysis_context(deal_id)
        await _report_progress(deal_id, "risk_analysis")

        node_fn = make_risk_analysis_worker_node(
            parent_log_id=_get_parent_log_id(deal_id, "run_risk_analysis"),
        )
        result = await node_fn(ctx.to_agent_state())

        ctx.risks = result.get("risks", [])
        ctx.risk_interdependencies = result.get("risk_interdependencies", [])
        if result.get("errors"):
            ctx.errors.extend(result["errors"])

        critical = [r for r in ctx.risks if r.get("severity") == "critical"]
        high = [r for r in ctx.risks if r.get("severity") == "high"]
        return (
            f"Risk analysis complete. "
            f"Total risks: {len(ctx.risks)} "
            f"(critical: {len(critical)}, high: {len(high)}). "
            f"Interdependencies: {len(ctx.risk_interdependencies)}"
        )
    except Exception as exc:
        logger.exception("run_risk_analysis failed for deal %s", deal_id)
        ctx = get_analysis_context(deal_id)
        ctx.errors.append(f"risk_analysis: {exc}")
        return f"ERROR: Risk analysis failed: {exc}. Proceed with other results."


@tool(args_schema=DealIdInput)
async def run_similar_project_search(deal_id: str) -> str:
    """Search for similar past projects and extract lessons learned.
    Requires deal_structuring to have been completed first."""
    try:
        from backend.app.agent.workers.similar_project import make_similar_project_worker_node

        ctx = get_analysis_context(deal_id)
        await _report_progress(deal_id, "similar_project")

        node_fn = make_similar_project_worker_node(
            parent_log_id=_get_parent_log_id(deal_id, "run_similar_project_search"),
        )
        result = await node_fn(ctx.to_agent_state())

        ctx.similar_projects = result.get("similar_projects", [])
        if result.get("errors"):
            ctx.errors.extend(result["errors"])

        return f"Similar project search complete. Found {len(ctx.similar_projects)} similar projects."
    except Exception as exc:
        logger.exception("run_similar_project_search failed for deal %s", deal_id)
        ctx = get_analysis_context(deal_id)
        ctx.errors.append(f"similar_project: {exc}")
        return f"ERROR: Similar project search failed: {exc}. Proceed with other results."


@tool(args_schema=FinalVerdictInput)
async def run_final_verdict(deal_id: str, hold: bool = False) -> str:
    """Generate the final executive report and verdict.
    Must be called last, after all other analyses are complete.
    Set hold=true for hold verdict when critical fields are missing."""
    ctx = get_analysis_context(deal_id)
    await _report_progress(deal_id, "final_verdict")

    if hold:
        raw_missing = ctx.structured_deal.get("missing_fields", [])
        missing = [f for f in raw_missing if f in CRITICAL_FIELDS]
        ctx.verdict = "pending"
        ctx.total_score = 0.0
        ctx.final_report = (
            "# 분석 보류\n\n"
            f"필수 항목이 충분하지 않아 분석을 보류합니다.\n\n"
            f"**미입력 항목:** {', '.join(missing) if missing else '(없음)'}"
        )
        return f"Hold verdict generated. Missing fields: {', '.join(missing)}"

    from backend.app.agent.workers.final_verdict import make_final_verdict_worker_node

    node_fn = make_final_verdict_worker_node(
        parent_log_id=_get_parent_log_id(deal_id, "run_final_verdict"),
    )
    result = await node_fn(ctx.to_agent_state())

    ctx.final_report = result.get("final_report", "")
    if result.get("errors"):
        ctx.errors.extend(result["errors"])

    return f"Final verdict generated. Verdict: {ctx.verdict}, Score: {ctx.total_score:.1f}"


@tool(args_schema=CompanyContextInput)
async def lookup_company_context(query: str) -> str:
    """Quick company context lookup without invoking a full worker.
    Use this for ad-hoc context queries during orchestration planning."""
    from backend.app.agent.tools import search_company_context

    return await search_company_context.ainvoke({"query": query})


META_TOOLS = [
    run_deal_structuring,
    run_scoring_analysis,
    run_resource_estimation,
    run_risk_analysis,
    run_similar_project_search,
    run_final_verdict,
    lookup_company_context,
]
