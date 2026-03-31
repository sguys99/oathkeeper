"""Tests for AnalysisContext lifecycle."""

import pytest

from backend.app.agent.orchestrator.context import (
    cleanup_analysis_context,
    get_analysis_context,
    init_analysis_context,
)

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _clean_registry():
    """Ensure no leftover context between tests."""
    yield
    for did in ["deal-1", "deal-2", "deal-3"]:
        cleanup_analysis_context(did)


class TestInitAndGet:
    def test_init_and_get(self):
        ctx = init_analysis_context("deal-1", "some input")
        assert get_analysis_context("deal-1") is ctx
        assert ctx.deal_id == "deal-1"
        assert ctx.deal_input == "some input"

    def test_get_uninitialized_raises(self):
        with pytest.raises(RuntimeError, match="not initialized"):
            get_analysis_context("nonexistent")

    def test_defaults(self):
        ctx = init_analysis_context("deal-1", "input")
        assert ctx.structured_deal == {}
        assert ctx.scores == []
        assert ctx.total_score == 0.0
        assert ctx.verdict == "pending"
        assert ctx.errors == []
        assert ctx.final_report == ""


class TestCleanup:
    def test_cleanup_returns_result_and_removes(self):
        ctx = init_analysis_context("deal-1", "input")
        ctx.total_score = 75.0
        ctx.verdict = "go"

        result = cleanup_analysis_context("deal-1")

        assert result is not None
        assert result["total_score"] == 75.0
        assert result["verdict"] == "go"
        # Should be gone now
        assert cleanup_analysis_context("deal-1") is None

    def test_cleanup_nonexistent_returns_none(self):
        assert cleanup_analysis_context("nonexistent") is None


class TestToResultDict:
    def test_contains_all_fields(self):
        ctx = init_analysis_context("deal-1", "input")
        ctx.structured_deal = {"customer_name": "Acme"}
        ctx.scores = [{"criterion": "Tech Fit", "score": 80}]
        ctx.total_score = 72.5
        ctx.verdict = "go"
        ctx.risks = [{"category": "technical"}]

        result = ctx.to_result_dict()

        assert result["structured_deal"] == {"customer_name": "Acme"}
        assert result["scores"] == [{"criterion": "Tech Fit", "score": 80}]
        assert result["total_score"] == 72.5
        assert result["verdict"] == "go"
        assert result["risks"] == [{"category": "technical"}]
        assert result["resource_estimate"] == {}
        assert result["similar_projects"] == []
        assert result["final_report"] == ""


class TestToAgentState:
    def test_includes_deal_id_and_input(self):
        ctx = init_analysis_context("deal-1", "raw deal text")
        ctx.structured_deal = {"customer_name": "Acme"}

        state = ctx.to_agent_state()

        assert state["deal_id"] == "deal-1"
        assert state["deal_input"] == "raw deal text"
        assert state["structured_deal"] == {"customer_name": "Acme"}
        assert state["scores"] == []
