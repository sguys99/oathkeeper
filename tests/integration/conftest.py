"""Integration test fixtures — real DB, mocked LLM and external services."""

import json
import os
import uuid
from unittest.mock import AsyncMock, patch

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # noqa: E402

from backend.app.api.main import app  # noqa: E402
from backend.app.api.schemas.notion import NotionSaveResponse  # noqa: E402
from backend.app.db.models.scoring_criteria import ScoringCriteria  # noqa: E402
from backend.app.db.models.team_member import TeamMember  # noqa: E402
from backend.app.db.session import get_db  # noqa: E402
from tests.fixtures.sample_llm_responses import (  # noqa: E402
    FINAL_REPORT_MARKDOWN,
    RESOURCE_ESTIMATION_RESPONSE,
    RISK_ANALYSIS_RESPONSE,
    SCORING_RESPONSE,
    SIMILAR_PROJECTS_RESPONSE,
    STRUCTURED_DEAL_HOLD_RESPONSE,
    STRUCTURED_DEAL_RESPONSE,
)

# ── HTTP Client ──────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def integration_client(db_session):
    """httpx AsyncClient wired to the FastAPI app with test DB."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


# ── BackgroundTask session patching ──────────────────────────────────────


@pytest.fixture
def patch_analysis_session(db_engine):
    """Route AnalysisService's own AsyncSessionLocal to the test engine.

    Without this, the background task creates sessions against the production
    DB (or a missing one), not the in-memory SQLite test DB.
    """
    test_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    with (
        patch("backend.app.agent.service.AsyncSessionLocal", test_factory),
        patch("backend.app.api.routers.analysis.AsyncSessionLocal", test_factory),
        patch("backend.app.db.session.AsyncSessionLocal", test_factory),
    ):
        yield


# ── LLM Mock ─────────────────────────────────────────────────────────────


def _llm_dispatch(system_prompt: str, user_prompt: str, *, llm=None) -> str:
    """Return canned JSON/markdown based on unique keywords in the system prompt.

    Each prompt YAML has a distinctive phrase; we match from most specific
    to least specific to avoid false positives from the shared system_base.
    """
    sp = system_prompt
    # deal_structuring — "비구조화된 Deal 텍스트에서"
    if "비구조화된" in sp:
        return STRUCTURED_DEAL_RESPONSE
    # scoring — "0~100점으로 평가"
    if "0~100점" in sp:
        return SCORING_RESPONSE
    # resource_estimation — "투입 인력 구성, 기간, 소요 예산을 산출"
    if "소요 예산을 산출" in sp:
        return RESOURCE_ESTIMATION_RESPONSE
    # risk_analysis — "카테고리로 분류하여 식별"
    if "카테고리로 분류" in sp:
        return RISK_ANALYSIS_RESPONSE
    # similar_project — "유사 프로젝트 정보를 현재 Deal과 비교"
    if "유사 프로젝트 정보를 현재" in sp:
        return SIMILAR_PROJECTS_RESPONSE
    # final_verdict — "경영진이 바로 읽을 수 있는 분석 리포트를 마크다운으로"
    if "마크다운으로 작성" in sp:
        return FINAL_REPORT_MARKDOWN
    return json.dumps({"result": "mock_fallback"})


def _llm_dispatch_hold(system_prompt: str, user_prompt: str, *, llm=None) -> str:
    """Variant that returns a hold-path structured deal."""
    if "비구조화된" in system_prompt:
        return STRUCTURED_DEAL_HOLD_RESPONSE
    return _llm_dispatch(system_prompt, user_prompt, llm=llm)


_CALL_LLM_TARGETS = [
    "backend.app.agent.nodes.deal_structuring.call_llm",
    "backend.app.agent.nodes.scoring.call_llm",
    "backend.app.agent.nodes.resource_estimation.call_llm",
    "backend.app.agent.nodes.risk_analysis.call_llm",
    "backend.app.agent.nodes.similar_project.call_llm",
    "backend.app.agent.nodes.final_verdict.call_llm",
]


@pytest.fixture
def mock_llm():
    """Patch call_llm at every node import site."""
    mock = AsyncMock(side_effect=_llm_dispatch)
    patches = [patch(target, mock) for target in _CALL_LLM_TARGETS]
    for p in patches:
        p.start()
    yield mock
    for p in patches:
        p.stop()


@pytest.fixture
def mock_llm_hold():
    """Patch call_llm to trigger the hold (missing fields) path."""
    mock = AsyncMock(side_effect=_llm_dispatch_hold)
    patches = [patch(target, mock) for target in _CALL_LLM_TARGETS]
    for p in patches:
        p.start()
    yield mock
    for p in patches:
        p.stop()


# ── Vector Store Mocks ───────────────────────────────────────────────────


@pytest.fixture
def mock_vector_stores():
    """Patch Pinecone vector stores to return empty/canned results."""
    ctx_query = AsyncMock(return_value=[])
    ctx_upsert = AsyncMock(return_value="vec-id-1")
    proj_search = AsyncMock(return_value=[])

    with (
        patch("backend.app.agent.nodes.deal_structuring.CompanyContextStore") as ctx_cls,
        patch("backend.app.agent.nodes.scoring.CompanyContextStore") as ctx_cls2,
        patch("backend.app.agent.nodes.risk_analysis.CompanyContextStore") as ctx_cls3,
        patch("backend.app.agent.nodes.similar_project.ProjectHistoryStore") as proj_cls,
        patch("backend.app.agent.nodes.resource_estimation.ProjectHistoryStore") as proj_cls2,
        patch("backend.app.agent.graph.CompanyContextStore") as graph_ctx,
        patch("backend.app.agent.graph.ProjectHistoryStore") as graph_proj,
    ):
        for cls in (ctx_cls, ctx_cls2, ctx_cls3, graph_ctx):
            inst = cls.return_value
            inst.query = ctx_query
            inst.upsert = ctx_upsert

        for cls in (proj_cls, proj_cls2, graph_proj):
            inst = cls.return_value
            inst.search_similar = proj_search

        yield {"context_query": ctx_query, "project_search": proj_search}


# ── Notion / Slack Mocks ────────────────────────────────────────────────


@pytest.fixture
def mock_notion_service():
    """Patch notion_service functions used by API routers."""
    mock_list = AsyncMock(
        return_value=[
            {
                "page_id": "notion-page-001",
                "deal_info": "xx철강 AI 프로젝트",
                "customer_name": "xx철강",
                "expected_amount": 500_000_000,
                "duration_months": 6,
                "author": "김영수",
                "status": "미분석",
            },
        ],
    )
    mock_save = AsyncMock(
        return_value=NotionSaveResponse(
            success=True,
            decision_page_id="decision-page-001",
            notion_page_url="https://www.notion.so/decision-page-001",
            saved_at="2026-03-12T10:00:00Z",
        ),
    )

    with (
        patch("backend.app.api.routers.notion.notion_service") as ns,
    ):
        ns.list_deals = mock_list
        ns.save_analysis_to_notion = mock_save
        yield ns


@pytest.fixture
def mock_slack_client():
    """Patch Slack notification to do nothing."""
    mock_send = AsyncMock(return_value=True)
    with patch("backend.app.api.routers.notion.slack_client") as sc:
        sc.send_analysis_notification = mock_send
        yield sc


# ── Seed Data ────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def seeded_db(db_session):
    """Insert 7 scoring criteria + company settings + sample team member."""
    from datetime import UTC, datetime

    from backend.app.db.models.company_setting import CompanySetting
    from backend.app.db.seed import COMPANY_SETTINGS_DEFAULTS, SCORING_CRITERIA_DEFAULTS

    now = datetime.now(UTC)

    # Insert scoring criteria with explicit is_active=True
    # (SQLite doesn't evaluate server_default in ORM inserts)
    for item in SCORING_CRITERIA_DEFAULTS:
        db_session.add(
            ScoringCriteria(id=uuid.uuid4(), **item, is_active=True, updated_at=now),
        )

    for item in COMPANY_SETTINGS_DEFAULTS:
        db_session.add(CompanySetting(**item, updated_at=now))

    member = TeamMember(
        id=uuid.uuid4(),
        name="테스트 MLE",
        role="MLE",
        monthly_rate=8_000_000,
        is_available=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add(member)
    await db_session.flush()
    yield db_session
