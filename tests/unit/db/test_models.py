"""Tests for ORM model creation and relationships."""

import uuid

import pytest

from backend.app.db.models.analysis_result import AnalysisResult
from backend.app.db.models.company_setting import CompanySetting
from backend.app.db.models.deal import Deal
from backend.app.db.models.scoring_criteria import ScoringCriteria
from backend.app.db.models.team_member import TeamMember
from backend.app.db.models.user import User

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_create_user(db_session):
    user = User(id=uuid.uuid4(), email="test@example.com", name="Test User", role="admin")
    db_session.add(user)
    await db_session.flush()

    fetched = await db_session.get(User, user.id)
    assert fetched is not None
    assert fetched.email == "test@example.com"
    assert fetched.role == "admin"


@pytest.mark.asyncio
async def test_create_deal(db_session):
    user = User(id=uuid.uuid4(), email="deal@example.com", name="Deal User", role="sales")
    db_session.add(user)
    await db_session.flush()

    deal = Deal(
        id=uuid.uuid4(),
        title="Test Deal",
        raw_input="Some raw input text",
        status="pending",
        created_by=user.id,
    )
    db_session.add(deal)
    await db_session.flush()

    fetched = await db_session.get(Deal, deal.id)
    assert fetched is not None
    assert fetched.title == "Test Deal"
    assert fetched.status == "pending"
    assert fetched.created_by == user.id


@pytest.mark.asyncio
async def test_deal_user_relationship(db_session):
    user = User(id=uuid.uuid4(), email="rel@example.com", name="Rel User", role="executive")
    db_session.add(user)
    await db_session.flush()

    deal = Deal(
        id=uuid.uuid4(),
        title="Relationship Deal",
        status="pending",
        created_by=user.id,
    )
    db_session.add(deal)
    await db_session.flush()

    fetched_deal = await db_session.get(Deal, deal.id)
    assert fetched_deal.created_by == user.id


@pytest.mark.asyncio
async def test_create_analysis_result(db_session):
    deal = Deal(id=uuid.uuid4(), title="Analysis Deal", status="completed")
    db_session.add(deal)
    await db_session.flush()

    analysis = AnalysisResult(
        id=uuid.uuid4(),
        deal_id=deal.id,
        total_score=75.50,
        verdict="go",
        scores={"기술_적합성": {"score": 85, "reasoning": "Good fit"}},
        report_markdown="# Report",
    )
    db_session.add(analysis)
    await db_session.flush()

    fetched = await db_session.get(AnalysisResult, analysis.id)
    assert fetched is not None
    assert float(fetched.total_score) == 75.50
    assert fetched.verdict == "go"
    assert fetched.scores["기술_적합성"]["score"] == 85


@pytest.mark.asyncio
async def test_create_scoring_criteria(db_session):
    criteria = ScoringCriteria(
        id=uuid.uuid4(),
        name="기술 적합성",
        weight=0.200,
        description="Test description",
        display_order=1,
    )
    db_session.add(criteria)
    await db_session.flush()

    fetched = await db_session.get(ScoringCriteria, criteria.id)
    assert fetched is not None
    assert fetched.name == "기술 적합성"
    assert float(fetched.weight) == 0.200


@pytest.mark.asyncio
async def test_create_company_setting(db_session):
    setting = CompanySetting(
        key="test_key",
        value="test_value",
        description="A test setting",
    )
    db_session.add(setting)
    await db_session.flush()

    fetched = await db_session.get(CompanySetting, "test_key")
    assert fetched is not None
    assert fetched.value == "test_value"


@pytest.mark.asyncio
async def test_create_team_member(db_session):
    member = TeamMember(
        id=uuid.uuid4(),
        name="김개발",
        role="BE",
        monthly_rate=8000000,
        is_available=True,
    )
    db_session.add(member)
    await db_session.flush()

    fetched = await db_session.get(TeamMember, member.id)
    assert fetched is not None
    assert fetched.name == "김개발"
    assert fetched.monthly_rate == 8000000
    assert fetched.is_available is True
