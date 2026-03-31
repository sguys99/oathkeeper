"""Tests for agent_log_repo — hierarchical logging fields."""

import uuid
from datetime import UTC, datetime

import pytest

from backend.app.db.models.deal import Deal
from backend.app.db.models.user import User
from backend.app.db.repositories import agent_log_repo

pytestmark = pytest.mark.unit


# ── Helpers ──────────────────────────────────────────────────────────


async def _create_deal(session) -> uuid.UUID:
    user = User(id=uuid.uuid4(), email="test@example.com", name="Test", role="admin")
    session.add(user)
    await session.flush()
    deal = Deal(
        id=uuid.uuid4(),
        title="Test Deal",
        raw_input="test",
        status="pending",
        created_by=user.id,
    )
    session.add(deal)
    await session.flush()
    return deal.id


# ── create() ─────────────────────────────────────────────────────────


class TestCreate:
    @pytest.mark.asyncio
    async def test_create_with_new_fields(self, db_session):
        deal_id = await _create_deal(db_session)
        now = datetime.now(UTC)

        log = await agent_log_repo.create(
            db_session,
            deal_id=deal_id,
            node_name="scoring:reasoning",
            started_at=now,
            parent_log_id=None,
            step_type="reasoning",
            step_index=0,
            tool_name=None,
            worker_name="scoring",
        )

        assert log.step_type == "reasoning"
        assert log.step_index == 0
        assert log.worker_name == "scoring"
        assert log.parent_log_id is None
        assert log.tool_name is None

    @pytest.mark.asyncio
    async def test_create_without_new_fields_backward_compat(self, db_session):
        deal_id = await _create_deal(db_session)
        now = datetime.now(UTC)

        log = await agent_log_repo.create(
            db_session,
            deal_id=deal_id,
            node_name="scoring",
            started_at=now,
        )

        assert log.step_type is None
        assert log.step_index is None
        assert log.worker_name is None
        assert log.parent_log_id is None
        assert log.tool_name is None

    @pytest.mark.asyncio
    async def test_create_with_parent_log_id(self, db_session):
        deal_id = await _create_deal(db_session)
        now = datetime.now(UTC)

        parent = await agent_log_repo.create(
            db_session,
            deal_id=deal_id,
            node_name="orchestrator",
            started_at=now,
            step_type="orchestrator_tool_call",
        )

        child = await agent_log_repo.create(
            db_session,
            deal_id=deal_id,
            node_name="scoring",
            started_at=now,
            step_type="worker_start",
            parent_log_id=parent.id,
            worker_name="scoring",
        )

        assert child.parent_log_id == parent.id

    @pytest.mark.asyncio
    async def test_create_tool_call_with_tool_name(self, db_session):
        deal_id = await _create_deal(db_session)
        now = datetime.now(UTC)

        log = await agent_log_repo.create(
            db_session,
            deal_id=deal_id,
            node_name="scoring:tool_call",
            started_at=now,
            step_type="tool_call",
            tool_name="calculate_weighted_score",
            worker_name="scoring",
            step_index=3,
        )

        assert log.tool_name == "calculate_weighted_score"
        assert log.step_index == 3


# ── update_log() ─────────────────────────────────────────────────────


class TestUpdateLog:
    @pytest.mark.asyncio
    async def test_update_log_partial(self, db_session):
        deal_id = await _create_deal(db_session)
        now = datetime.now(UTC)

        log = await agent_log_repo.create(
            db_session,
            deal_id=deal_id,
            node_name="orchestrator",
            started_at=now,
            step_type="orchestrator_tool_call",
        )

        completed = datetime.now(UTC)
        updated = await agent_log_repo.update_log(
            db_session,
            log.id,
            raw_output="Worker completed",
            duration_ms=1500,
            completed_at=completed,
        )

        assert updated is not None
        assert updated.raw_output == "Worker completed"
        assert updated.duration_ms == 1500
        assert updated.completed_at == completed

    @pytest.mark.asyncio
    async def test_update_log_not_found(self, db_session):
        result = await agent_log_repo.update_log(
            db_session,
            uuid.uuid4(),
            raw_output="test",
        )
        assert result is None


# ── list_by_deal_id_with_children() ──────────────────────────────────


class TestListByDealIdWithChildren:
    @pytest.mark.asyncio
    async def test_returns_logs_with_children(self, db_session):
        deal_id = await _create_deal(db_session)
        now = datetime.now(UTC)

        parent = await agent_log_repo.create(
            db_session,
            deal_id=deal_id,
            node_name="orchestrator",
            started_at=now,
            step_type="orchestrator_tool_call",
        )
        await agent_log_repo.create(
            db_session,
            deal_id=deal_id,
            node_name="scoring",
            started_at=now,
            step_type="worker_start",
            parent_log_id=parent.id,
            worker_name="scoring",
        )
        await db_session.flush()

        logs = await agent_log_repo.list_by_deal_id_with_children(db_session, deal_id)
        assert len(logs) == 2


# ── list_root_logs_by_deal_id() ──────────────────────────────────────


class TestListRootLogsByDealId:
    @pytest.mark.asyncio
    async def test_returns_only_root_logs(self, db_session):
        deal_id = await _create_deal(db_session)
        now = datetime.now(UTC)

        parent = await agent_log_repo.create(
            db_session,
            deal_id=deal_id,
            node_name="orchestrator",
            started_at=now,
            step_type="orchestrator_reasoning",
        )
        await agent_log_repo.create(
            db_session,
            deal_id=deal_id,
            node_name="scoring",
            started_at=now,
            step_type="worker_start",
            parent_log_id=parent.id,
        )
        await db_session.flush()

        roots = await agent_log_repo.list_root_logs_by_deal_id(db_session, deal_id)
        assert len(roots) == 1
        assert roots[0].id == parent.id
