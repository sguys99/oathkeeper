"""API test fixtures — httpx AsyncClient with test DB session."""

import os

# Set a valid DATABASE_URL before any app imports trigger engine creation.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from backend.app.api.main import app  # noqa: E402
from backend.app.db.session import get_db  # noqa: E402


@pytest_asyncio.fixture
async def async_client(db_session):
    """Provide an httpx AsyncClient wired to the test DB session."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
