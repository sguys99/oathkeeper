"""Tests for agent log schemas — hierarchical logging fields."""

import uuid
from datetime import UTC, datetime

import pytest

from backend.app.api.schemas.agent_log import (
    AgentLogResponse,
    AgentLogTreeNode,
    AgentLogTreeResponse,
)

pytestmark = pytest.mark.unit


class TestAgentLogResponse:
    def test_new_fields_default_to_none(self):
        """Old logs without new fields should serialize with None defaults."""
        resp = AgentLogResponse(
            id=uuid.uuid4(),
            deal_id=uuid.uuid4(),
            node_name="scoring",
            started_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
        )
        assert resp.parent_log_id is None
        assert resp.step_type is None
        assert resp.step_index is None
        assert resp.tool_name is None
        assert resp.worker_name is None

    def test_new_fields_populated(self):
        parent_id = uuid.uuid4()
        resp = AgentLogResponse(
            id=uuid.uuid4(),
            deal_id=uuid.uuid4(),
            node_name="scoring:tool_call",
            started_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
            parent_log_id=parent_id,
            step_type="tool_call",
            step_index=2,
            tool_name="calculate_weighted_score",
            worker_name="scoring",
        )
        assert resp.parent_log_id == parent_id
        assert resp.step_type == "tool_call"
        assert resp.step_index == 2
        assert resp.tool_name == "calculate_weighted_score"
        assert resp.worker_name == "scoring"


class TestAgentLogTreeNode:
    def test_children_default_empty(self):
        node = AgentLogTreeNode(
            id=uuid.uuid4(),
            deal_id=uuid.uuid4(),
            node_name="orchestrator",
            started_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
            step_type="orchestrator_reasoning",
        )
        assert node.children == []

    def test_nested_children(self):
        child = AgentLogTreeNode(
            id=uuid.uuid4(),
            deal_id=uuid.uuid4(),
            node_name="scoring:reasoning",
            started_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
            step_type="reasoning",
            worker_name="scoring",
        )
        parent = AgentLogTreeNode(
            id=uuid.uuid4(),
            deal_id=uuid.uuid4(),
            node_name="orchestrator",
            started_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
            step_type="orchestrator_tool_call",
            children=[child],
        )
        assert len(parent.children) == 1
        assert parent.children[0].worker_name == "scoring"


class TestAgentLogTreeResponse:
    def test_structure(self):
        deal_id = uuid.uuid4()
        resp = AgentLogTreeResponse(
            deal_id=deal_id,
            logs=[],
            total_count=0,
            total_duration_ms=0,
        )
        assert resp.deal_id == deal_id
        assert resp.logs == []
        assert resp.total_count == 0
