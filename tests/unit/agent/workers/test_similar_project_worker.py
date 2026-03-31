"""Tests for similar_project ReAct worker."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.agent.workers.similar_project import (
    _build_search_query,
    make_similar_project_worker_node,
)

pytestmark = pytest.mark.unit


def _make_mocks():
    mock_tpl = MagicMock()
    mock_tpl.render_system.return_value = "system"
    mock_tpl.render_user.return_value = "user"
    return mock_tpl


class TestBuildSearchQuery:
    def test_builds_from_structured_deal(self):
        deal = {
            "project_overview": {"objective": "AI 챗봇", "scope": "고객 응대"},
            "tech_requirements": ["Python", "LangChain"],
            "customer_industry": "금융",
        }
        query = _build_search_query(deal)
        assert "AI 챗봇" in query
        assert "고객 응대" in query
        assert "Python" in query
        assert "금융" in query

    def test_empty_deal_returns_empty(self):
        assert _build_search_query({}) == ""

    def test_string_overview(self):
        deal = {"project_overview": "간단한 프로젝트 설명"}
        query = _build_search_query(deal)
        assert "간단한 프로젝트 설명" in query


class TestSimilarProjectWorkerNode:
    @pytest.mark.asyncio
    @patch("backend.app.agent.workers.similar_project.invoke_worker", new_callable=AsyncMock)
    @patch("backend.app.agent.workers.similar_project.make_react_worker")
    @patch("backend.app.agent.workers.similar_project.get_llm")
    @patch("backend.app.agent.workers.similar_project.load_prompt")
    async def test_happy_path(self, mock_load_prompt, mock_get_llm, mock_make_worker, mock_invoke):
        mock_load_prompt.return_value = _make_mocks()
        mock_get_llm.return_value = MagicMock()
        mock_make_worker.return_value = MagicMock()

        mock_invoke.return_value = json.dumps(
            {
                "similar_projects": [
                    {
                        "project_name": "과거 AI 프로젝트",
                        "relevance_score": 0.85,
                        "key_comparisons": ["유사 기술 스택"],
                    },
                ],
            },
        )

        node = make_similar_project_worker_node()
        result = await node(
            {
                "structured_deal": {
                    "project_overview": {"objective": "AI 솔루션"},
                    "customer_industry": "IT",
                },
                "deal_id": str(uuid.uuid4()),
            },
        )

        assert len(result["similar_projects"]) == 1
        assert result["similar_projects"][0]["relevance_score"] == 0.85

    @pytest.mark.asyncio
    @patch("backend.app.agent.workers.similar_project.log_node_skip", new_callable=AsyncMock)
    async def test_skip_on_empty_query(self, mock_skip):
        node = make_similar_project_worker_node()
        result = await node(
            {
                "structured_deal": {},
                "deal_id": str(uuid.uuid4()),
            },
        )

        assert result["similar_projects"] == []
        mock_skip.assert_called_once()

    @pytest.mark.asyncio
    @patch("backend.app.agent.workers.similar_project.log_node_skip", new_callable=AsyncMock)
    @patch("backend.app.agent.workers.similar_project.invoke_worker", new_callable=AsyncMock)
    @patch("backend.app.agent.workers.similar_project.make_react_worker")
    @patch("backend.app.agent.workers.similar_project.get_llm")
    @patch("backend.app.agent.workers.similar_project.load_prompt")
    async def test_error_logs_skip_and_returns_empty(
        self,
        mock_load_prompt,
        mock_get_llm,
        mock_make_worker,
        mock_invoke,
        mock_skip,
    ):
        mock_load_prompt.return_value = _make_mocks()
        mock_get_llm.return_value = MagicMock()
        mock_make_worker.return_value = MagicMock()
        mock_invoke.side_effect = RuntimeError("failed")

        node = make_similar_project_worker_node()
        result = await node(
            {
                "structured_deal": {
                    "project_overview": {"objective": "test"},
                },
                "deal_id": str(uuid.uuid4()),
            },
        )

        assert result["similar_projects"] == []
        assert "similar_project" in result["errors"][0]
        mock_skip.assert_called_once()
