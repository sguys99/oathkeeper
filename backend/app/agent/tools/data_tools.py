"""Data tools — internal data retrieval from DB and vector stores."""

import json
import logging
import uuid

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from backend.app.agent.base import (
    fetch_company_settings,
    format_company_context,
    format_scoring_criteria,
    format_team_members,
)
from backend.app.agent.tools._context import get_tool_context
from backend.app.db.repositories import analysis_repo, settings_repo

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# search_similar_projects
# ---------------------------------------------------------------------------


class SearchSimilarProjectsInput(BaseModel):
    """Search for similar past projects in the vector database."""

    query: str = Field(description="Deal description text to search against")
    top_k: int = Field(default=3, description="Number of results (1-10)", ge=1, le=10)
    industry: str | None = Field(default=None, description="Optional industry filter")


@tool(args_schema=SearchSimilarProjectsInput)
async def search_similar_projects(
    query: str,
    top_k: int = 3,
    industry: str | None = None,
) -> str:
    """Search for similar past projects by semantic similarity. Returns project names,
    similarity scores, industry, tech stack, duration, headcount, and contract amounts."""
    try:
        ctx = get_tool_context()
        results = await ctx.project_history_store.search_similar(query, top_k=top_k, industry=industry)
        return json.dumps(results, ensure_ascii=False, default=str)
    except Exception as e:
        logger.exception("search_similar_projects failed")
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# search_company_context
# ---------------------------------------------------------------------------


class SearchCompanyContextInput(BaseModel):
    """Search company internal context documents."""

    query: str = Field(description="Search query text")
    top_k: int = Field(default=5, description="Number of results (1-10)", ge=1, le=10)
    context_type: str | None = Field(
        default=None,
        description="Filter by type: cost_table, strategy, regulation, tech_stack",
    )


@tool(args_schema=SearchCompanyContextInput)
async def search_company_context(
    query: str,
    top_k: int = 5,
    context_type: str | None = None,
) -> str:
    """Search company internal knowledge base for relevant context. Returns documents
    with relevance scores, content, and type classifications."""
    try:
        ctx = get_tool_context()
        results = await ctx.company_context_store.query(query, top_k=top_k, context_type=context_type)
        formatted = format_company_context(results)
        return json.dumps(
            {"documents": results, "formatted": formatted},
            ensure_ascii=False,
        )
    except Exception as e:
        logger.exception("search_company_context failed")
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# get_team_members
# ---------------------------------------------------------------------------


@tool
async def get_team_members() -> str:
    """Get current team members with their roles, rates, availability, and assignments."""
    try:
        ctx = get_tool_context()
        async with ctx.session_factory() as db:
            members = await settings_repo.list_team_members(db)
        formatted = format_team_members(members)
        return json.dumps(formatted, ensure_ascii=False, default=str)
    except Exception as e:
        logger.exception("get_team_members failed")
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# get_scoring_criteria
# ---------------------------------------------------------------------------


@tool
async def get_scoring_criteria() -> str:
    """Get active scoring criteria with names, weights, and descriptions."""
    try:
        ctx = get_tool_context()
        async with ctx.session_factory() as db:
            criteria = await settings_repo.list_active_criteria(db)
        formatted = format_scoring_criteria(criteria)
        return json.dumps(formatted, ensure_ascii=False, default=str)
    except Exception as e:
        logger.exception("get_scoring_criteria failed")
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# get_company_settings
# ---------------------------------------------------------------------------


@tool
async def get_company_settings() -> str:
    """Get company settings: business direction, deal criteria, short-term strategy."""
    try:
        ctx = get_tool_context()
        async with ctx.session_factory() as db:
            settings = await fetch_company_settings(db)
        return json.dumps(settings, ensure_ascii=False)
    except Exception as e:
        logger.exception("get_company_settings failed")
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# get_past_deal_analysis
# ---------------------------------------------------------------------------


class GetPastDealAnalysisInput(BaseModel):
    """Retrieve a past deal's analysis result."""

    deal_id: str = Field(description="UUID of the deal to look up")


@tool(args_schema=GetPastDealAnalysisInput)
async def get_past_deal_analysis(deal_id: str) -> str:
    """Get the full analysis result for a past deal, including scores, resource estimates,
    risks, similar projects, and the final verdict."""
    try:
        ctx = get_tool_context()
        async with ctx.session_factory() as db:
            result = await analysis_repo.get_by_deal_id(db, uuid.UUID(deal_id))
        if result is None:
            return json.dumps({"error": "No analysis found for this deal"})
        return json.dumps(
            {
                "total_score": float(result.total_score) if result.total_score else None,
                "verdict": result.verdict,
                "scores": result.scores,
                "resource_estimate": result.resource_estimate,
                "risks": result.risks,
                "similar_projects": result.similar_projects,
            },
            ensure_ascii=False,
            default=str,
        )
    except ValueError:
        return json.dumps({"error": f"Invalid UUID: {deal_id}"})
    except Exception as e:
        logger.exception("get_past_deal_analysis failed")
        return json.dumps({"error": str(e)})
