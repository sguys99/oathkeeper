"""E2E test fixtures — real LLM, real DB, real vector store."""

import asyncio
import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.db.base import Base

# ---------------------------------------------------------------------------
# Skip-if-no-credentials
# ---------------------------------------------------------------------------

_REQUIRED_VARS = ["DATABASE_URL"]
_LLM_VARS = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]


def _check_env():
    for var in _REQUIRED_VARS:
        if not os.environ.get(var):
            pytest.skip(f"E2E: {var} not set")
    if not any(os.environ.get(v) for v in _LLM_VARS):
        pytest.skip(f"E2E: need one of {_LLM_VARS}")


# ---------------------------------------------------------------------------
# Database fixtures (real PostgreSQL)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="module")
async def e2e_engine():
    _check_env()
    url = os.environ["DATABASE_URL"]
    engine = create_async_engine(url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def e2e_session(e2e_engine):
    factory = async_sessionmaker(
        bind=e2e_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with factory() as session:
        yield session
        await session.rollback()


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def e2e_client(e2e_session):
    from backend.app.api.main import app
    from backend.app.db.session import get_db

    async def override_get_db():
        yield e2e_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def ensure_seed_data(e2e_session):
    from backend.app.db.seed import seed_company_settings, seed_scoring_criteria

    await seed_scoring_criteria(e2e_session)
    await seed_company_settings(e2e_session)
    await e2e_session.commit()


# ---------------------------------------------------------------------------
# Polling helper
# ---------------------------------------------------------------------------


async def poll_until_complete(
    client: AsyncClient,
    deal_id: str,
    *,
    interval: float = 5.0,
    timeout: float = 180.0,
) -> dict:
    """Poll GET /api/deals/{id} until status is completed or failed."""
    elapsed = 0.0
    while elapsed < timeout:
        resp = await client.get(f"/api/deals/{deal_id}")
        assert resp.status_code == 200
        data = resp.json()
        if data["status"] in ("completed", "failed"):
            return data
        await asyncio.sleep(interval)
        elapsed += interval
    pytest.fail(f"Deal {deal_id} did not complete within {timeout}s")
