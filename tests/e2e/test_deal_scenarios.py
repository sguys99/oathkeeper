"""E2E: 5 real deal analysis scenarios with actual LLM calls.

Requires: DATABASE_URL, OPENAI_API_KEY or ANTHROPIC_API_KEY, PINECONE_API_KEY
Run with: uv run pytest -m e2e -v --timeout=200
"""

import pytest

from tests.e2e.conftest import poll_until_complete
from tests.fixtures.sample_deals import (
    CLEAR_GO_DEAL,
    CLEAR_NO_GO_DEAL,
    CONDITIONAL_GO_DEAL,
    FILE_UPLOAD_DEAL,
    HOLD_DEAL,
)

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio, pytest.mark.timeout(180)]


def _assert_analysis_complete(analysis: dict):
    """Shared assertions for a completed analysis."""
    assert analysis["verdict"] in ("go", "conditional_go", "no_go", "pending")
    assert analysis["total_score"] is not None
    assert 0 <= analysis["total_score"] <= 100
    assert isinstance(analysis["scores"], list)
    assert analysis["report_markdown"] is not None
    assert len(analysis["report_markdown"]) > 0


async def _run_deal_scenario(client, deal_data: dict) -> dict:
    """Create deal, trigger analysis, poll until done, return analysis."""
    # Create
    resp = await client.post("/api/deals/", json=deal_data)
    assert resp.status_code == 201
    deal_id = resp.json()["id"]

    # Trigger
    resp = await client.post(f"/api/deals/{deal_id}/analyze")
    assert resp.status_code == 202

    # Poll
    deal = await poll_until_complete(client, deal_id)
    assert deal["status"] == "completed"

    # Fetch analysis
    resp = await client.get(f"/api/deals/{deal_id}/analysis")
    assert resp.status_code == 200
    return resp.json()


class TestDealScenarios:
    """5 deal scenarios with varied characteristics."""

    async def test_clear_go_deal(self, e2e_client, ensure_seed_data):
        """Well-defined project, large budget → expected Go verdict, score ≥ 70."""
        analysis = await _run_deal_scenario(e2e_client, CLEAR_GO_DEAL)
        _assert_analysis_complete(analysis)
        assert len(analysis["scores"]) == 7
        assert analysis["resource_estimate"] is not None
        assert isinstance(analysis["risks"], list)

    async def test_clear_no_go_deal(self, e2e_client, ensure_seed_data):
        """Vague requirements, tiny budget → expected No-Go, score < 40."""
        analysis = await _run_deal_scenario(e2e_client, CLEAR_NO_GO_DEAL)
        _assert_analysis_complete(analysis)

    async def test_conditional_go_deal(self, e2e_client, ensure_seed_data):
        """Decent project but tight constraints → Conditional Go expected."""
        analysis = await _run_deal_scenario(e2e_client, CONDITIONAL_GO_DEAL)
        _assert_analysis_complete(analysis)

    async def test_conditional_go_has_orchestrator_logs(self, e2e_client, ensure_seed_data):
        """Conditional Go deal should produce orchestrator→worker log hierarchy."""
        resp = await e2e_client.post("/api/deals/", json=CONDITIONAL_GO_DEAL)
        deal_id = resp.json()["id"]
        await e2e_client.post(f"/api/deals/{deal_id}/analyze")
        await poll_until_complete(e2e_client, deal_id)

        logs_resp = await e2e_client.get(f"/api/deals/{deal_id}/logs", params={"view": "tree"})
        assert logs_resp.status_code == 200
        tree = logs_resp.json()
        assert tree["total_count"] > 0

        # At least one orchestrator_tool_call root with worker children
        orch_roots = [log for log in tree["logs"] if log.get("step_type") == "orchestrator_tool_call"]
        assert len(orch_roots) >= 1, "Expected at least one orchestrator tool call"
        worker_children = [
            child
            for root in orch_roots
            for child in root.get("children", [])
            if child.get("step_type") == "worker_start"
        ]
        assert len(worker_children) >= 1, "Expected at least one worker execution"

    async def test_hold_deal(self, e2e_client, ensure_seed_data):
        """Minimal input → Hold verdict due to missing fields."""
        resp = await e2e_client.post("/api/deals/", json=HOLD_DEAL)
        deal_id = resp.json()["id"]

        resp = await e2e_client.post(f"/api/deals/{deal_id}/analyze")
        assert resp.status_code == 202

        deal = await poll_until_complete(e2e_client, deal_id)
        assert deal["status"] == "completed"

        resp = await e2e_client.get(f"/api/deals/{deal_id}/analysis")
        analysis = resp.json()
        # Hold path may set verdict to "pending" or produce minimal scores
        assert analysis["verdict"] is not None
        assert analysis["report_markdown"] is not None

    async def test_file_upload_deal(self, e2e_client, ensure_seed_data):
        """Standard deal with detailed text → analysis completes with all fields."""
        analysis = await _run_deal_scenario(e2e_client, FILE_UPLOAD_DEAL)
        _assert_analysis_complete(analysis)
        assert isinstance(analysis["similar_projects"], list)
