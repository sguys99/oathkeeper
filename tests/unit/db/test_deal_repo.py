"""Tests for deal repository."""

import uuid

import pytest

from backend.app.db.models.user import User
from backend.app.db.repositories import deal_repo

pytestmark = pytest.mark.unit


async def _create_user(session) -> User:
    user = User(id=uuid.uuid4(), email=f"{uuid.uuid4().hex[:8]}@test.com", name="Test", role="sales")
    session.add(user)
    await session.flush()
    return user


@pytest.mark.asyncio
async def test_create_deal(db_session):
    user = await _create_user(db_session)
    deal = await deal_repo.create(
        db_session,
        title="New Deal",
        raw_input="Some input",
        created_by=user.id,
    )
    assert deal.id is not None
    assert deal.title == "New Deal"
    assert deal.status == "pending"


@pytest.mark.asyncio
async def test_get_by_id(db_session):
    deal = await deal_repo.create(db_session, title="Find Me")
    fetched = await deal_repo.get_by_id(db_session, deal.id)
    assert fetched is not None
    assert fetched.title == "Find Me"


@pytest.mark.asyncio
async def test_get_by_id_not_found(db_session):
    result = await deal_repo.get_by_id(db_session, uuid.uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_list_with_filters_no_filter(db_session):
    await deal_repo.create(db_session, title="Deal A")
    await deal_repo.create(db_session, title="Deal B")
    deals = await deal_repo.list_with_filters(db_session)
    assert len(deals) >= 2


@pytest.mark.asyncio
async def test_list_with_filters_by_status(db_session):
    deal = await deal_repo.create(db_session, title="Status Deal")
    await deal_repo.update_status(db_session, deal.id, "analyzing")

    analyzing = await deal_repo.list_with_filters(db_session, status="analyzing")
    assert any(d.id == deal.id for d in analyzing)

    pending = await deal_repo.list_with_filters(db_session, status="pending")
    assert not any(d.id == deal.id for d in pending)


@pytest.mark.asyncio
async def test_update_status(db_session):
    deal = await deal_repo.create(db_session, title="Update Me")
    assert deal.status == "pending"

    updated = await deal_repo.update_status(db_session, deal.id, "completed")
    assert updated is not None
    assert updated.status == "completed"


@pytest.mark.asyncio
async def test_update_status_not_found(db_session):
    result = await deal_repo.update_status(db_session, uuid.uuid4(), "completed")
    assert result is None


@pytest.mark.asyncio
async def test_list_with_pagination(db_session):
    for i in range(5):
        await deal_repo.create(db_session, title=f"Page Deal {i}")

    page1 = await deal_repo.list_with_filters(db_session, limit=2)
    page2 = await deal_repo.list_with_filters(db_session, offset=2, limit=2)
    assert len(page1) == 2
    assert len(page2) == 2
    assert page1[0].id != page2[0].id
