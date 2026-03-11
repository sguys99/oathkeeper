"""Schema validation tests."""

import uuid

import pytest
from pydantic import ValidationError

from backend.app.api.schemas.analysis import VerdictEnum
from backend.app.api.schemas.deal import DealCreate, DealStatus
from backend.app.api.schemas.settings import (
    TeamMemberCreate,
    WeightUpdateItem,
    WeightUpdateRequest,
)
from backend.app.api.schemas.user import UserCreate

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# WeightUpdateRequest
# ---------------------------------------------------------------------------


def test_weight_update_valid():
    items = [
        WeightUpdateItem(id=uuid.uuid4(), weight=0.2),
        WeightUpdateItem(id=uuid.uuid4(), weight=0.2),
        WeightUpdateItem(id=uuid.uuid4(), weight=0.15),
        WeightUpdateItem(id=uuid.uuid4(), weight=0.15),
        WeightUpdateItem(id=uuid.uuid4(), weight=0.1),
        WeightUpdateItem(id=uuid.uuid4(), weight=0.1),
        WeightUpdateItem(id=uuid.uuid4(), weight=0.1),
    ]
    req = WeightUpdateRequest(weights=items)
    assert len(req.weights) == 7


def test_weight_update_invalid_sum():
    items = [
        WeightUpdateItem(id=uuid.uuid4(), weight=0.5),
        WeightUpdateItem(id=uuid.uuid4(), weight=0.3),
    ]
    with pytest.raises(ValidationError, match="sum to 1.0"):
        WeightUpdateRequest(weights=items)


def test_weight_update_tolerance():
    """Sum very close to 1.0 should pass within tolerance."""
    items = [
        WeightUpdateItem(id=uuid.uuid4(), weight=0.2),
        WeightUpdateItem(id=uuid.uuid4(), weight=0.2),
        WeightUpdateItem(id=uuid.uuid4(), weight=0.15),
        WeightUpdateItem(id=uuid.uuid4(), weight=0.15),
        WeightUpdateItem(id=uuid.uuid4(), weight=0.1),
        WeightUpdateItem(id=uuid.uuid4(), weight=0.1),
        WeightUpdateItem(id=uuid.uuid4(), weight=0.1005),
    ]
    req = WeightUpdateRequest(weights=items)
    assert len(req.weights) == 7


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


def test_deal_status_values():
    assert set(DealStatus) == {
        DealStatus.pending,
        DealStatus.analyzing,
        DealStatus.completed,
        DealStatus.failed,
    }


def test_verdict_enum_values():
    assert set(VerdictEnum) == {
        VerdictEnum.go,
        VerdictEnum.conditional_go,
        VerdictEnum.no_go,
        VerdictEnum.pending,
    }


# ---------------------------------------------------------------------------
# DealCreate
# ---------------------------------------------------------------------------


def test_deal_create_minimal():
    deal = DealCreate(title="Test Deal")
    assert deal.title == "Test Deal"
    assert deal.raw_input is None
    assert deal.notion_page_id is None
    assert deal.created_by is None


# ---------------------------------------------------------------------------
# TeamMemberCreate
# ---------------------------------------------------------------------------


def test_team_member_create_invalid_rate():
    with pytest.raises(ValidationError):
        TeamMemberCreate(name="Test", role="BE", monthly_rate=0)


def test_team_member_create_negative_rate():
    with pytest.raises(ValidationError):
        TeamMemberCreate(name="Test", role="BE", monthly_rate=-100)


# ---------------------------------------------------------------------------
# UserCreate
# ---------------------------------------------------------------------------


def test_user_create_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(email="not-an-email", name="Test", role="admin")


def test_user_create_invalid_role():
    with pytest.raises(ValidationError):
        UserCreate(email="test@example.com", name="Test", role="superadmin")


def test_user_create_valid():
    user = UserCreate(email="test@example.com", name="Test User", role="sales")
    assert user.email == "test@example.com"
    assert user.role == "sales"
