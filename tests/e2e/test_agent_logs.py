"""E2E checks for hierarchical agent logs and status stream contract."""

import json

import pytest

from tests.e2e.conftest import poll_until_complete
from tests.fixtures.sample_deals import CLEAR_GO_DEAL

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio, pytest.mark.timeout(180)]


async def test_analysis_exposes_tree_logs_and_terminal_status_event(
    e2e_client,
    ensure_seed_data,
):
    create_resp = await e2e_client.post("/api/deals/", json=CLEAR_GO_DEAL)
    assert create_resp.status_code == 201
    deal_id = create_resp.json()["id"]

    trigger_resp = await e2e_client.post(f"/api/deals/{deal_id}/analyze")
    assert trigger_resp.status_code == 202

    deal = await poll_until_complete(e2e_client, deal_id)
    assert deal["status"] == "completed"

    logs_resp = await e2e_client.get(f"/api/deals/{deal_id}/logs", params={"view": "tree"})
    assert logs_resp.status_code == 200
    tree = logs_resp.json()
    assert tree["total_count"] > 0
    assert len(tree["logs"]) > 0
    assert any(
        child["step_type"] == "worker_start"
        for root in tree["logs"]
        for child in root.get("children", [])
    )

    async with e2e_client.stream("GET", f"/api/deals/{deal_id}/status") as resp:
        assert resp.status_code == 200
        events = [
            json.loads(line.removeprefix("data: "))
            async for line in resp.aiter_lines()
            if line.startswith("data: ")
        ]

    assert events[-1]["status"] == "completed"
    assert events[-1]["current_step"] is None
