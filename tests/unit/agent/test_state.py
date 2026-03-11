"""Tests for AgentState TypedDict."""

import pytest

from backend.app.agent.state import AgentState

pytestmark = pytest.mark.unit


class TestAgentState:
    def test_partial_dict_is_valid(self):
        """Nodes can return partial dicts (total=False)."""
        partial: AgentState = {"deal_input": "test deal"}
        assert partial["deal_input"] == "test deal"

    def test_all_fields_assignable(self):
        state: AgentState = {
            "deal_input": "raw text",
            "structured_deal": {"customer_name": "Acme"},
            "scores": [{"criterion": "tech", "score": 80}],
            "total_score": 75.0,
            "verdict": "go",
            "resource_estimate": {"duration_months": 3},
            "risks": [{"category": "technical", "level": "HIGH"}],
            "similar_projects": [],
            "final_report": "# Report",
            "status": "completed",
            "errors": [],
        }
        assert state["verdict"] == "go"
        assert state["total_score"] == 75.0

    def test_errors_field_supports_list(self):
        state: AgentState = {"errors": ["err1", "err2"]}
        assert len(state["errors"]) == 2
