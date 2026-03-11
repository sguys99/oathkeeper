"""Settings endpoint tests."""

import uuid

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


# ---------------------------------------------------------------------------
# Company Settings
# ---------------------------------------------------------------------------


async def test_upsert_company_setting(async_client: AsyncClient):
    resp = await async_client.put(
        "/api/settings/company",
        json={"key": "test_key", "value": "test_value", "description": "A test setting"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["key"] == "test_key"
    assert data["value"] == "test_value"


async def test_upsert_company_setting_update(async_client: AsyncClient):
    await async_client.put(
        "/api/settings/company",
        json={"key": "update_key", "value": "v1"},
    )
    resp = await async_client.put(
        "/api/settings/company",
        json={"key": "update_key", "value": "v2"},
    )
    assert resp.status_code == 200
    assert resp.json()["value"] == "v2"


async def test_get_company_setting(async_client: AsyncClient):
    await async_client.put(
        "/api/settings/company",
        json={"key": "get_key", "value": "get_value"},
    )
    resp = await async_client.get("/api/settings/company/get_key")
    assert resp.status_code == 200
    assert resp.json()["value"] == "get_value"


async def test_get_company_setting_not_found(async_client: AsyncClient):
    resp = await async_client.get("/api/settings/company/nonexistent")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Team Members
# ---------------------------------------------------------------------------


async def test_create_team_member(async_client: AsyncClient):
    resp = await async_client.post(
        "/api/settings/team-members",
        json={"name": "Kim", "role": "BE", "monthly_rate": 8000000},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Kim"
    assert data["role"] == "BE"
    assert data["monthly_rate"] == 8000000
    assert data["is_available"] is True


async def test_create_team_member_invalid_role(async_client: AsyncClient):
    resp = await async_client.post(
        "/api/settings/team-members",
        json={"name": "Kim", "role": "INVALID", "monthly_rate": 8000000},
    )
    assert resp.status_code == 422


async def test_update_team_member(async_client: AsyncClient):
    create_resp = await async_client.post(
        "/api/settings/team-members",
        json={"name": "Lee", "role": "FE", "monthly_rate": 7000000},
    )
    member_id = create_resp.json()["id"]
    resp = await async_client.put(
        f"/api/settings/team-members/{member_id}",
        json={"monthly_rate": 7500000},
    )
    assert resp.status_code == 200
    assert resp.json()["monthly_rate"] == 7500000


async def test_update_team_member_not_found(async_client: AsyncClient):
    fake_id = uuid.uuid4()
    resp = await async_client.put(
        f"/api/settings/team-members/{fake_id}",
        json={"name": "Ghost"},
    )
    assert resp.status_code == 404


async def test_delete_team_member(async_client: AsyncClient):
    create_resp = await async_client.post(
        "/api/settings/team-members",
        json={"name": "Park", "role": "PM", "monthly_rate": 9000000},
    )
    member_id = create_resp.json()["id"]
    resp = await async_client.delete(f"/api/settings/team-members/{member_id}")
    assert resp.status_code == 204


async def test_delete_team_member_not_found(async_client: AsyncClient):
    fake_id = uuid.uuid4()
    resp = await async_client.delete(f"/api/settings/team-members/{fake_id}")
    assert resp.status_code == 404


async def test_list_team_members(async_client: AsyncClient):
    await async_client.post(
        "/api/settings/team-members",
        json={"name": "A", "role": "BE", "monthly_rate": 8000000},
    )
    resp = await async_client.get("/api/settings/team-members")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


# ---------------------------------------------------------------------------
# Scoring Criteria
# ---------------------------------------------------------------------------


async def test_list_criteria(async_client: AsyncClient):
    resp = await async_client.get("/api/settings/criteria")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_update_weights_invalid_sum(async_client: AsyncClient):
    resp = await async_client.put(
        "/api/settings/criteria/weights",
        json={
            "weights": [
                {"id": str(uuid.uuid4()), "weight": 0.5},
                {"id": str(uuid.uuid4()), "weight": 0.3},
            ],
        },
    )
    assert resp.status_code == 422
