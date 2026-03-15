import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.exceptions import OathKeeperError, oathkeeper_exception_handler
from backend.app.api.routers import agent_logs, analysis, deals, notion, prompts, settings, users
from backend.app.db.session import engine
from backend.app.utils.logging import setup_logging
from backend.app.utils.settings import get_settings

app_settings = get_settings()
logger = structlog.stdlib.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging(app_settings)

    if app_settings.sentry_dsn:
        import sentry_sdk

        sentry_sdk.init(
            dsn=app_settings.sentry_dsn,
            environment=app_settings.environment,
            traces_sample_rate=0.1,
            send_default_pii=False,
        )

    logger.info("app_started", environment=app_settings.environment)
    yield
    # Shutdown
    await engine.dispose()
    logger.info("app_stopped")


app = FastAPI(
    title=app_settings.app_name,
    version=app_settings.app_version,
    debug=app_settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if app_settings.debug else app_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(OathKeeperError, oathkeeper_exception_handler)

app.include_router(users.router)
app.include_router(deals.router)
app.include_router(analysis.router)
app.include_router(agent_logs.router)
app.include_router(settings.router)
app.include_router(notion.router)
app.include_router(prompts.router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=duration_ms,
    )
    return response


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": app_settings.app_version}
