from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.exceptions import OathKeeperError, oathkeeper_exception_handler
from backend.app.api.routers import analysis, deals, notion, settings, users
from backend.app.db.session import engine
from backend.app.utils.settings import get_settings

app_settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title=app_settings.app_name,
    version=app_settings.app_version,
    debug=app_settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if app_settings.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(OathKeeperError, oathkeeper_exception_handler)

app.include_router(users.router)
app.include_router(deals.router)
app.include_router(analysis.router)
app.include_router(settings.router)
app.include_router(notion.router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": app_settings.app_version}
