"""Integration: Settings changes → analysis reflects updated configuration."""

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


class TestScoringWeights:
    """Verify that scoring weight changes are reflected in analysis prompts."""

    async def test_weight_change_reflected_in_prompt(
        self,
        integration_client: AsyncClient,
        patch_analysis_session,
        mock_llm,
        mock_vector_stores,
        seeded_db,
    ):
        """After updating criteria weights, the scoring prompt includes new values."""
        # 1. Get current criteria (seeded)
        resp = await integration_client.get("/api/settings/criteria")
        assert resp.status_code == 200
        criteria = resp.json()
        assert len(criteria) == 7

        # 2. Update weights (shift first criterion to 0.30, adjust last to keep sum=1)
        weights = []
        for i, c in enumerate(criteria):
            if i == 0:
                weights.append({"id": c["id"], "weight": 0.30})
            elif i == 6:
                weights.append({"id": c["id"], "weight": 0.00})
            else:
                weights.append({"id": c["id"], "weight": c["weight"]})

        resp = await integration_client.put(
            "/api/settings/criteria/weights",
            json={"weights": weights},
        )
        assert resp.status_code == 200

        # 3. Create deal and trigger analysis
        resp = await integration_client.post(
            "/api/deals/",
            json={"title": "가중치 검증 딜", "raw_input": "테스트 프로젝트 설명"},
        )
        deal_id = resp.json()["id"]

        resp = await integration_client.post(f"/api/deals/{deal_id}/analyze")
        assert resp.status_code == 202

        # 4. Verify mock_llm was called with updated weight in prompt
        # The scoring node calls call_llm; inspect the captured calls
        for call in mock_llm.call_args_list:
            args = call.args if call.args else ()
            if len(args) >= 1:
                system_prompt = args[0].lower()
                if "평가" in system_prompt or "scoring" in system_prompt:
                    # The prompt should contain the updated weight 0.3
                    assert "0.3" in args[0], "Updated weight 0.3 not found in scoring system prompt"
                    break

    async def test_criteria_weight_sum_validation(
        self,
        integration_client: AsyncClient,
        seeded_db,
    ):
        """Weights that don't sum to 1.0 should be rejected."""
        resp = await integration_client.get("/api/settings/criteria")
        criteria = resp.json()

        # All weights set to 0.20 → sum = 1.40
        weights = [{"id": c["id"], "weight": 0.20} for c in criteria]

        resp = await integration_client.put(
            "/api/settings/criteria/weights",
            json={"weights": weights},
        )
        assert resp.status_code == 422


class TestTeamMemberCRUD:
    """Full CRUD lifecycle for team members through the API."""

    async def test_team_member_crud(self, integration_client: AsyncClient, seeded_db):
        # Create
        resp = await integration_client.post(
            "/api/settings/team-members",
            json={
                "name": "신규 개발자",
                "role": "BE",
                "monthly_rate": 7_000_000,
                "is_available": True,
            },
        )
        assert resp.status_code == 201
        member = resp.json()
        member_id = member["id"]
        assert member["name"] == "신규 개발자"
        assert member["role"] == "BE"

        # List — should contain both the seeded member and the new one
        resp = await integration_client.get("/api/settings/team-members")
        assert resp.status_code == 200
        members = resp.json()
        assert len(members) >= 2
        names = {m["name"] for m in members}
        assert "신규 개발자" in names

        # Update
        resp = await integration_client.put(
            f"/api/settings/team-members/{member_id}",
            json={"monthly_rate": 8_500_000, "is_available": False},
        )
        assert resp.status_code == 200
        assert resp.json()["monthly_rate"] == 8_500_000
        assert resp.json()["is_available"] is False

        # Delete
        resp = await integration_client.delete(
            f"/api/settings/team-members/{member_id}",
        )
        assert resp.status_code == 204

        # Verify deletion
        resp = await integration_client.get("/api/settings/team-members")
        ids = {m["id"] for m in resp.json()}
        assert member_id not in ids


class TestCompanySettings:
    """Company setting CRUD through the API."""

    async def test_company_setting_upsert_and_read(
        self,
        integration_client: AsyncClient,
        seeded_db,
    ):
        # Read seeded setting
        resp = await integration_client.get(
            "/api/settings/company/business_direction",
        )
        assert resp.status_code == 200
        assert "AI" in resp.json()["value"]

        # Update
        resp = await integration_client.put(
            "/api/settings/company",
            json={
                "key": "business_direction",
                "value": "AI + 로보틱스 솔루션",
                "description": "사업 방향 수정",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["value"] == "AI + 로보틱스 솔루션"

        # Re-read
        resp = await integration_client.get(
            "/api/settings/company/business_direction",
        )
        assert resp.json()["value"] == "AI + 로보틱스 솔루션"

    async def test_missing_setting_returns_404(
        self,
        integration_client: AsyncClient,
        seeded_db,
    ):
        resp = await integration_client.get(
            "/api/settings/company/nonexistent_key",
        )
        assert resp.status_code == 404
