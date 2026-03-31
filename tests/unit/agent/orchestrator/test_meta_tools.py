"""Tests for orchestrator meta-tools."""

from unittest.mock import AsyncMock, patch

import pytest

from backend.app.agent.orchestrator.context import (
    cleanup_analysis_context,
    get_analysis_context,
    init_analysis_context,
)
from backend.app.agent.orchestrator.meta_tools import (
    run_deal_structuring,
    run_final_verdict,
    run_resource_estimation,
    run_risk_analysis,
    run_scoring_analysis,
    run_similar_project_search,
)

pytestmark = pytest.mark.unit

DEAL_ID = "test-deal-1"


@pytest.fixture(autouse=True)
def _clean_context():
    """Ensure no leftover context between tests."""
    yield
    cleanup_analysis_context(DEAL_ID)


# ── run_deal_structuring ─────────────────────────────────────────────


class TestRunDealStructuring:
    @pytest.mark.asyncio
    async def test_happy_path(self):
        init_analysis_context(DEAL_ID, "raw deal text")

        fake_result = {
            "structured_deal": {
                "customer_name": "Acme",
                "customer_industry": "핀테크",
                "missing_fields": [],
            },
            "status": "deal_structured",
        }

        with patch(
            "backend.app.agent.workers.deal_structuring.make_deal_structuring_worker_node",
        ) as mock_factory:
            mock_node = AsyncMock(return_value=fake_result)
            mock_factory.return_value = mock_node

            result_str = await run_deal_structuring.ainvoke({"deal_id": DEAL_ID})

        assert "HOLD_RECOMMENDED" not in result_str
        assert "Deal structured successfully" in result_str

        ctx = get_analysis_context(DEAL_ID)
        assert ctx.structured_deal["customer_name"] == "Acme"

    @pytest.mark.asyncio
    async def test_hold_path(self):
        init_analysis_context(DEAL_ID, "vague deal")

        fake_result = {
            "structured_deal": {
                "missing_fields": [
                    "customer_name",
                    "expected_amount",
                    "duration_months",
                ],
            },
        }

        with patch(
            "backend.app.agent.workers.deal_structuring.make_deal_structuring_worker_node",
        ) as mock_factory:
            mock_node = AsyncMock(return_value=fake_result)
            mock_factory.return_value = mock_node

            result_str = await run_deal_structuring.ainvoke({"deal_id": DEAL_ID})

        assert "HOLD_RECOMMENDED" in result_str
        assert "3 critical fields missing" in result_str

    @pytest.mark.asyncio
    async def test_worker_error_stores_errors(self):
        init_analysis_context(DEAL_ID, "deal")

        fake_result = {
            "structured_deal": {},
            "errors": ["deal_structuring: worker execution failed"],
            "status": "failed",
        }

        with patch(
            "backend.app.agent.workers.deal_structuring.make_deal_structuring_worker_node",
        ) as mock_factory:
            mock_node = AsyncMock(return_value=fake_result)
            mock_factory.return_value = mock_node

            await run_deal_structuring.ainvoke({"deal_id": DEAL_ID})

        ctx = get_analysis_context(DEAL_ID)
        assert len(ctx.errors) == 1
        assert "worker execution failed" in ctx.errors[0]


# ── run_scoring_analysis ─────────────────────────────────────────────


class TestRunScoringAnalysis:
    @pytest.mark.asyncio
    async def test_stores_scores_in_context(self):
        ctx = init_analysis_context(DEAL_ID, "deal")
        ctx.structured_deal = {"customer_name": "Acme"}

        fake_result = {
            "scores": [
                {
                    "criterion": "기술 적합성",
                    "score": 80,
                    "weight": 0.2,
                    "weighted_score": 16.0,
                },
            ],
            "total_score": 72.5,
            "verdict": "go",
        }

        with patch(
            "backend.app.agent.workers.scoring.make_scoring_worker_node",
        ) as mock_factory:
            mock_node = AsyncMock(return_value=fake_result)
            mock_factory.return_value = mock_node

            result_str = await run_scoring_analysis.ainvoke({"deal_id": DEAL_ID})

        assert ctx.total_score == 72.5
        assert ctx.verdict == "go"
        assert "72.5" in result_str
        assert "go" in result_str


# ── run_resource_estimation ──────────────────────────────────────────


class TestRunResourceEstimation:
    @pytest.mark.asyncio
    async def test_stores_estimate_in_context(self):
        ctx = init_analysis_context(DEAL_ID, "deal")
        ctx.structured_deal = {"customer_name": "Acme"}

        fake_result = {
            "resource_estimate": {
                "profitability": {"expected_margin": 25.0},
                "team_composition": [{"role": "PM"}, {"role": "Dev"}],
                "cost_breakdown": {"total_cost": 30000},
            },
        }

        with patch(
            "backend.app.agent.workers.resource_estimation.make_resource_estimation_worker_node",
        ) as mock_factory:
            mock_node = AsyncMock(return_value=fake_result)
            mock_factory.return_value = mock_node

            result_str = await run_resource_estimation.ainvoke({"deal_id": DEAL_ID})

        assert ctx.resource_estimate["profitability"]["expected_margin"] == 25.0
        assert "25.0" in result_str
        assert "2 members" in result_str


# ── run_risk_analysis ────────────────────────────────────────────────


class TestRunRiskAnalysis:
    @pytest.mark.asyncio
    async def test_stores_risks_in_context(self):
        ctx = init_analysis_context(DEAL_ID, "deal")
        ctx.structured_deal = {"customer_name": "Acme"}

        fake_result = {
            "risks": [
                {"category": "기술", "severity": "critical"},
                {"category": "일정", "severity": "high"},
                {"category": "고객", "severity": "medium"},
            ],
            "risk_interdependencies": [{"from": "기술", "to": "일정"}],
        }

        with patch(
            "backend.app.agent.workers.risk_analysis.make_risk_analysis_worker_node",
        ) as mock_factory:
            mock_node = AsyncMock(return_value=fake_result)
            mock_factory.return_value = mock_node

            result_str = await run_risk_analysis.ainvoke({"deal_id": DEAL_ID})

        assert len(ctx.risks) == 3
        assert len(ctx.risk_interdependencies) == 1
        assert "critical: 1" in result_str
        assert "high: 1" in result_str


# ── run_similar_project_search ───────────────────────────────────────


class TestRunSimilarProjectSearch:
    @pytest.mark.asyncio
    async def test_stores_projects_in_context(self):
        ctx = init_analysis_context(DEAL_ID, "deal")
        ctx.structured_deal = {"customer_name": "Acme"}

        fake_result = {
            "similar_projects": [
                {"project_name": "Project A", "relevance_score": 0.85},
            ],
        }

        with patch(
            "backend.app.agent.workers.similar_project.make_similar_project_worker_node",
        ) as mock_factory:
            mock_node = AsyncMock(return_value=fake_result)
            mock_factory.return_value = mock_node

            result_str = await run_similar_project_search.ainvoke({"deal_id": DEAL_ID})

        assert len(ctx.similar_projects) == 1
        assert "1 similar projects" in result_str


# ── run_final_verdict ────────────────────────────────────────────────


class TestRunFinalVerdict:
    @pytest.mark.asyncio
    async def test_normal_verdict(self):
        ctx = init_analysis_context(DEAL_ID, "deal")
        ctx.structured_deal = {"customer_name": "Acme"}
        ctx.total_score = 75.0
        ctx.verdict = "go"

        fake_result = {
            "final_report": "# 최종 보고서\n\n분석 완료.",
            "status": "completed",
        }

        with patch(
            "backend.app.agent.workers.final_verdict.make_final_verdict_worker_node",
        ) as mock_factory:
            mock_node = AsyncMock(return_value=fake_result)
            mock_factory.return_value = mock_node

            result_str = await run_final_verdict.ainvoke({"deal_id": DEAL_ID})

        assert ctx.final_report == "# 최종 보고서\n\n분석 완료."
        assert "Final verdict generated" in result_str

    @pytest.mark.asyncio
    async def test_hold_verdict(self):
        ctx = init_analysis_context(DEAL_ID, "vague deal")
        ctx.structured_deal = {
            "missing_fields": [
                "customer_name",
                "expected_amount",
                "duration_months",
            ],
        }

        result_str = await run_final_verdict.ainvoke(
            {"deal_id": DEAL_ID, "hold": True},
        )

        assert ctx.verdict == "pending"
        assert ctx.total_score == 0.0
        assert "분석 보류" in ctx.final_report
        assert "Hold verdict generated" in result_str

    @pytest.mark.asyncio
    async def test_worker_error_stores_errors(self):
        ctx = init_analysis_context(DEAL_ID, "deal")
        ctx.structured_deal = {"customer_name": "Acme"}

        fake_result = {
            "final_report": "",
            "errors": ["final_verdict: worker execution failed"],
            "status": "failed",
        }

        with patch(
            "backend.app.agent.workers.final_verdict.make_final_verdict_worker_node",
        ) as mock_factory:
            mock_node = AsyncMock(return_value=fake_result)
            mock_factory.return_value = mock_node

            await run_final_verdict.ainvoke({"deal_id": DEAL_ID})

        assert len(ctx.errors) == 1


# ── Progress callback ────────────────────────────────────────────────


class TestProgressCallback:
    @pytest.mark.asyncio
    async def test_progress_callback_called(self):
        progress_calls = []

        async def on_progress(label: str) -> None:
            progress_calls.append(label)

        init_analysis_context(DEAL_ID, "deal", on_progress=on_progress)

        fake_result = {
            "structured_deal": {"customer_name": "Acme", "missing_fields": []},
        }

        with patch(
            "backend.app.agent.workers.deal_structuring.make_deal_structuring_worker_node",
        ) as mock_factory:
            mock_node = AsyncMock(return_value=fake_result)
            mock_factory.return_value = mock_node

            await run_deal_structuring.ainvoke({"deal_id": DEAL_ID})

        assert "Deal 구조화 중..." in progress_calls
