"""Deal and analysis endpoint tests."""

import uuid

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


# ---------------------------------------------------------------------------
# Deal CRUD
# ---------------------------------------------------------------------------


async def test_create_deal(async_client: AsyncClient):
    resp = await async_client.post(
        "/api/deals/",
        json={"title": "New Deal", "raw_input": "Some text"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "New Deal"
    assert data["status"] == "pending"
    assert data["id"] is not None


async def test_create_deal_minimal(async_client: AsyncClient):
    resp = await async_client.post("/api/deals/", json={"title": "Minimal"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["raw_input"] is None
    assert data["notion_page_id"] is None


async def test_list_deals_empty(async_client: AsyncClient):
    resp = await async_client.get("/api/deals/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


async def test_list_deals_with_data(async_client: AsyncClient):
    await async_client.post("/api/deals/", json={"title": "Deal 1"})
    await async_client.post("/api/deals/", json={"title": "Deal 2"})
    resp = await async_client.get("/api/deals/")
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


async def test_list_deals_pagination(async_client: AsyncClient):
    for i in range(5):
        await async_client.post("/api/deals/", json={"title": f"Deal {i}"})
    resp = await async_client.get("/api/deals/", params={"offset": 0, "limit": 2})
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 2


async def test_get_deal_by_id(async_client: AsyncClient):
    create_resp = await async_client.post("/api/deals/", json={"title": "Test"})
    deal_id = create_resp.json()["id"]
    resp = await async_client.get(f"/api/deals/{deal_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Test"


async def test_get_deal_not_found(async_client: AsyncClient):
    fake_id = uuid.uuid4()
    resp = await async_client.get(f"/api/deals/{fake_id}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------


async def test_trigger_analysis_stub(async_client: AsyncClient):
    create_resp = await async_client.post(
        "/api/deals/",
        json={"title": "Analyze Me", "raw_input": "Test deal content for analysis"},
    )
    deal_id = create_resp.json()["id"]
    resp = await async_client.post(f"/api/deals/{deal_id}/analyze")
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "analyzing"
    assert data["message"].startswith("Analysis started")


async def test_trigger_analysis_not_found(async_client: AsyncClient):
    fake_id = uuid.uuid4()
    resp = await async_client.post(f"/api/deals/{fake_id}/analyze")
    assert resp.status_code == 404


async def test_trigger_analysis_empty_input(async_client: AsyncClient):
    create_resp = await async_client.post("/api/deals/", json={"title": "Empty"})
    deal_id = create_resp.json()["id"]
    resp = await async_client.post(f"/api/deals/{deal_id}/analyze")
    assert resp.status_code == 422


async def test_trigger_analysis_already_in_progress(async_client: AsyncClient):
    create_resp = await async_client.post(
        "/api/deals/",
        json={"title": "Busy", "raw_input": "Deal content"},
    )
    deal_id = create_resp.json()["id"]
    # First trigger
    resp1 = await async_client.post(f"/api/deals/{deal_id}/analyze")
    assert resp1.status_code == 202
    # Second trigger should fail
    resp2 = await async_client.post(f"/api/deals/{deal_id}/analyze")
    assert resp2.status_code == 409


async def test_get_analysis_not_found(async_client: AsyncClient):
    create_resp = await async_client.post("/api/deals/", json={"title": "No Analysis"})
    deal_id = create_resp.json()["id"]
    resp = await async_client.get(f"/api/deals/{deal_id}/analysis")
    assert resp.status_code == 404
