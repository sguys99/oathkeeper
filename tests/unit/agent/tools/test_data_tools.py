"""Unit tests for data tools."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.agent.tools.data_tools import (
    get_company_settings,
    get_past_deal_analysis,
    get_scoring_criteria,
    get_team_members,
    search_company_context,
    search_similar_projects,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_tool_context():
    """Create a mock ToolContext with all dependencies."""
    ctx = MagicMock()

    mock_session = AsyncMock()
    # session_factory() must return an async context manager
    async_cm = AsyncMock()
    async_cm.__aenter__.return_value = mock_session
    async_cm.__aexit__.return_value = False
    ctx.session_factory.return_value = async_cm

    ctx.company_context_store = AsyncMock()
    ctx.project_history_store = AsyncMock()

    return ctx, mock_session


# ---------------------------------------------------------------------------
# search_similar_projects
# ---------------------------------------------------------------------------


class TestSearchSimilarProjects:
    @pytest.mark.asyncio
    @patch("backend.app.agent.tools.data_tools.get_tool_context")
    async def test_returns_results(self, mock_get_ctx, mock_tool_context):
        ctx, _ = mock_tool_context
        mock_get_ctx.return_value = ctx
        ctx.project_history_store.search_similar.return_value = [
            {
                "project_name": "AI Platform",
                "similarity_score": 0.92,
                "industry": "IT",
            },
        ]

        result = await search_similar_projects.ainvoke({"query": "AI platform development", "top_k": 3})
        parsed = json.loads(result)

        assert len(parsed) == 1
        assert parsed[0]["project_name"] == "AI Platform"
        ctx.project_history_store.search_similar.assert_called_once_with(
            "AI platform development",
            top_k=3,
            industry=None,
        )

    @pytest.mark.asyncio
    @patch("backend.app.agent.tools.data_tools.get_tool_context")
    async def test_with_industry_filter(self, mock_get_ctx, mock_tool_context):
        ctx, _ = mock_tool_context
        mock_get_ctx.return_value = ctx
        ctx.project_history_store.search_similar.return_value = []

        result = await search_similar_projects.ainvoke(
            {"query": "test", "top_k": 5, "industry": "fintech"},
        )
        parsed = json.loads(result)

        assert parsed == []
        ctx.project_history_store.search_similar.assert_called_once_with(
            "test",
            top_k=5,
            industry="fintech",
        )

    @pytest.mark.asyncio
    @patch("backend.app.agent.tools.data_tools.get_tool_context")
    async def test_error_handling(self, mock_get_ctx, mock_tool_context):
        ctx, _ = mock_tool_context
        mock_get_ctx.return_value = ctx
        ctx.project_history_store.search_similar.side_effect = RuntimeError("connection failed")

        result = await search_similar_projects.ainvoke({"query": "test"})
        parsed = json.loads(result)

        assert "error" in parsed


# ---------------------------------------------------------------------------
# search_company_context
# ---------------------------------------------------------------------------


class TestSearchCompanyContext:
    @pytest.mark.asyncio
    @patch("backend.app.agent.tools.data_tools.get_tool_context")
    async def test_returns_documents_and_formatted(self, mock_get_ctx, mock_tool_context):
        ctx, _ = mock_tool_context
        mock_get_ctx.return_value = ctx
        ctx.company_context_store.query.return_value = [
            {"id": "1", "score": 0.9, "content": "AI strategy doc", "type": "strategy"},
        ]

        result = await search_company_context.ainvoke({"query": "AI strategy"})
        parsed = json.loads(result)

        assert "documents" in parsed
        assert "formatted" in parsed
        assert len(parsed["documents"]) == 1

    @pytest.mark.asyncio
    @patch("backend.app.agent.tools.data_tools.get_tool_context")
    async def test_with_context_type_filter(self, mock_get_ctx, mock_tool_context):
        ctx, _ = mock_tool_context
        mock_get_ctx.return_value = ctx
        ctx.company_context_store.query.return_value = []

        await search_company_context.ainvoke({"query": "costs", "context_type": "cost_table"})

        ctx.company_context_store.query.assert_called_once_with(
            "costs",
            top_k=5,
            context_type="cost_table",
        )

    @pytest.mark.asyncio
    @patch("backend.app.agent.tools.data_tools.get_tool_context")
    async def test_empty_results(self, mock_get_ctx, mock_tool_context):
        ctx, _ = mock_tool_context
        mock_get_ctx.return_value = ctx
        ctx.company_context_store.query.return_value = []

        result = await search_company_context.ainvoke({"query": "nonexistent"})
        parsed = json.loads(result)

        assert parsed["documents"] == []


# ---------------------------------------------------------------------------
# get_team_members
# ---------------------------------------------------------------------------


class TestGetTeamMembers:
    @pytest.mark.asyncio
    @patch("backend.app.agent.tools.data_tools.settings_repo")
    @patch("backend.app.agent.tools.data_tools.get_tool_context")
    async def test_returns_formatted_members(self, mock_get_ctx, mock_repo, mock_tool_context):
        ctx, mock_session = mock_tool_context
        mock_get_ctx.return_value = ctx

        mock_member = MagicMock()
        mock_member.name = "홍길동"
        mock_member.role = "Backend"
        mock_member.monthly_rate = 800
        mock_member.is_available = True
        mock_member.current_project = None
        mock_member.available_from = None
        mock_repo.list_team_members = AsyncMock(return_value=[mock_member])

        result = await get_team_members.ainvoke({})
        parsed = json.loads(result)

        assert len(parsed) == 1
        assert parsed[0]["name"] == "홍길동"
        assert parsed[0]["role"] == "Backend"

    @pytest.mark.asyncio
    @patch("backend.app.agent.tools.data_tools.settings_repo")
    @patch("backend.app.agent.tools.data_tools.get_tool_context")
    async def test_empty_team(self, mock_get_ctx, mock_repo, mock_tool_context):
        ctx, _ = mock_tool_context
        mock_get_ctx.return_value = ctx
        mock_repo.list_team_members = AsyncMock(return_value=[])

        result = await get_team_members.ainvoke({})
        parsed = json.loads(result)

        assert parsed == []


# ---------------------------------------------------------------------------
# get_scoring_criteria
# ---------------------------------------------------------------------------


class TestGetScoringCriteria:
    @pytest.mark.asyncio
    @patch("backend.app.agent.tools.data_tools.settings_repo")
    @patch("backend.app.agent.tools.data_tools.get_tool_context")
    async def test_returns_formatted_criteria(self, mock_get_ctx, mock_repo, mock_tool_context):
        ctx, _ = mock_tool_context
        mock_get_ctx.return_value = ctx

        mock_criterion = MagicMock()
        mock_criterion.name = "기술 적합성"
        mock_criterion.weight = 0.20
        mock_criterion.description = "기술 스택 적합도"
        mock_repo.list_active_criteria = AsyncMock(return_value=[mock_criterion])

        result = await get_scoring_criteria.ainvoke({})
        parsed = json.loads(result)

        assert len(parsed) == 1
        assert parsed[0]["name"] == "기술 적합성"
        assert parsed[0]["weight"] == 0.20

    @pytest.mark.asyncio
    @patch("backend.app.agent.tools.data_tools.settings_repo")
    @patch("backend.app.agent.tools.data_tools.get_tool_context")
    async def test_empty_criteria(self, mock_get_ctx, mock_repo, mock_tool_context):
        ctx, _ = mock_tool_context
        mock_get_ctx.return_value = ctx
        mock_repo.list_active_criteria = AsyncMock(return_value=[])

        result = await get_scoring_criteria.ainvoke({})
        parsed = json.loads(result)

        assert parsed == []


# ---------------------------------------------------------------------------
# get_company_settings
# ---------------------------------------------------------------------------


class TestGetCompanySettings:
    @pytest.mark.asyncio
    @patch("backend.app.agent.tools.data_tools.fetch_company_settings")
    @patch("backend.app.agent.tools.data_tools.get_tool_context")
    async def test_returns_settings(self, mock_get_ctx, mock_fetch, mock_tool_context):
        ctx, _ = mock_tool_context
        mock_get_ctx.return_value = ctx
        mock_fetch.return_value = {
            "business_direction": "AI 중심 사업 확장",
            "deal_criteria": "수익률 15% 이상",
            "short_term_strategy": "핵심 역량 강화",
        }

        result = await get_company_settings.ainvoke({})
        parsed = json.loads(result)

        assert parsed["business_direction"] == "AI 중심 사업 확장"
        assert "deal_criteria" in parsed
        assert "short_term_strategy" in parsed


# ---------------------------------------------------------------------------
# get_past_deal_analysis
# ---------------------------------------------------------------------------


class TestGetPastDealAnalysis:
    @pytest.mark.asyncio
    @patch("backend.app.agent.tools.data_tools.analysis_repo")
    @patch("backend.app.agent.tools.data_tools.get_tool_context")
    async def test_found(self, mock_get_ctx, mock_repo, mock_tool_context):
        ctx, _ = mock_tool_context
        mock_get_ctx.return_value = ctx

        mock_result = MagicMock()
        mock_result.total_score = 75.5
        mock_result.verdict = "go"
        mock_result.scores = [{"criterion": "test", "score": 80}]
        mock_result.resource_estimate = {"duration_months": 6}
        mock_result.risks = []
        mock_result.similar_projects = []
        mock_repo.get_by_deal_id = AsyncMock(return_value=mock_result)

        result = await get_past_deal_analysis.ainvoke(
            {"deal_id": "12345678-1234-1234-1234-123456789abc"},
        )
        parsed = json.loads(result)

        assert parsed["verdict"] == "go"
        assert parsed["total_score"] == 75.5

    @pytest.mark.asyncio
    @patch("backend.app.agent.tools.data_tools.analysis_repo")
    @patch("backend.app.agent.tools.data_tools.get_tool_context")
    async def test_not_found(self, mock_get_ctx, mock_repo, mock_tool_context):
        ctx, _ = mock_tool_context
        mock_get_ctx.return_value = ctx
        mock_repo.get_by_deal_id = AsyncMock(return_value=None)

        result = await get_past_deal_analysis.ainvoke(
            {"deal_id": "12345678-1234-1234-1234-123456789abc"},
        )
        parsed = json.loads(result)

        assert "error" in parsed
        assert "No analysis found" in parsed["error"]

    @pytest.mark.asyncio
    @patch("backend.app.agent.tools.data_tools.get_tool_context")
    async def test_invalid_uuid(self, mock_get_ctx, mock_tool_context):
        ctx, _ = mock_tool_context
        mock_get_ctx.return_value = ctx

        result = await get_past_deal_analysis.ainvoke({"deal_id": "not-a-uuid"})
        parsed = json.loads(result)

        assert "error" in parsed
        assert "Invalid UUID" in parsed["error"]
