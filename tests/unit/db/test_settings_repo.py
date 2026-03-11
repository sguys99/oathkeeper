"""Tests for settings repository (scoring criteria, company settings, team members)."""

import uuid
from datetime import date

import pytest

from backend.app.db.models.scoring_criteria import ScoringCriteria
from backend.app.db.repositories import settings_repo

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# ScoringCriteria
# ---------------------------------------------------------------------------


async def _seed_criteria(session, count=3):
    criteria = []
    for i in range(count):
        c = ScoringCriteria(
            id=uuid.uuid4(),
            name=f"Criteria {i}",
            weight=round(1.0 / count, 3),
            display_order=i + 1,
            is_active=True,
        )
        session.add(c)
        criteria.append(c)
    await session.flush()
    return criteria


@pytest.mark.asyncio
async def test_list_active_criteria(db_session):
    await _seed_criteria(db_session, 3)
    active = await settings_repo.list_active_criteria(db_session)
    assert len(active) >= 3
    assert all(c.is_active for c in active)


@pytest.mark.asyncio
async def test_update_weights(db_session):
    seeded = await _seed_criteria(db_session, 2)
    new_weights = [
        {"id": seeded[0].id, "weight": 0.600},
        {"id": seeded[1].id, "weight": 0.400},
    ]
    updated = await settings_repo.update_weights(db_session, new_weights)
    assert len(updated) == 2
    assert float(updated[0].weight) == 0.600
    assert float(updated[1].weight) == 0.400


# ---------------------------------------------------------------------------
# CompanySetting
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_setting_not_found(db_session):
    result = await settings_repo.get_setting(db_session, "nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_upsert_setting_create(db_session):
    setting = await settings_repo.upsert_setting(db_session, "new_key", "new_value", description="desc")
    assert setting.key == "new_key"
    assert setting.value == "new_value"


@pytest.mark.asyncio
async def test_upsert_setting_update(db_session):
    await settings_repo.upsert_setting(db_session, "upd_key", "v1")
    updated = await settings_repo.upsert_setting(db_session, "upd_key", "v2")
    assert updated.value == "v2"


# ---------------------------------------------------------------------------
# TeamMember
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_and_list_team_members(db_session):
    await settings_repo.create_team_member(db_session, name="Alice", role="PM", monthly_rate=10000000)
    await settings_repo.create_team_member(db_session, name="Bob", role="BE", monthly_rate=8000000)
    members = await settings_repo.list_team_members(db_session)
    assert len(members) >= 2


@pytest.mark.asyncio
async def test_update_team_member(db_session):
    member = await settings_repo.create_team_member(
        db_session,
        name="Charlie",
        role="FE",
        monthly_rate=7000000,
    )
    updated = await settings_repo.update_team_member(
        db_session,
        member.id,
        is_available=False,
        current_project="Project X",
        available_from=date(2026, 6, 1),
    )
    assert updated is not None
    assert updated.is_available is False
    assert updated.current_project == "Project X"
    assert updated.available_from == date(2026, 6, 1)


@pytest.mark.asyncio
async def test_update_team_member_not_found(db_session):
    result = await settings_repo.update_team_member(db_session, uuid.uuid4(), name="Ghost")
    assert result is None


@pytest.mark.asyncio
async def test_delete_team_member(db_session):
    member = await settings_repo.create_team_member(
        db_session,
        name="Delete Me",
        role="DevOps",
        monthly_rate=9000000,
    )
    deleted = await settings_repo.delete_team_member(db_session, member.id)
    assert deleted is True

    deleted_again = await settings_repo.delete_team_member(db_session, member.id)
    assert deleted_again is False
