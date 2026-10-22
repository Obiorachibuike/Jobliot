"""CareerPilot AI backend - FastAPI application entry point."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.database import init_engine, run_migrations
from app.core.security import sanitize_error
from app.services.tasks import scheduler as task_scheduler
from app.services.tasks.manager import task_manager

logger = logging.getLogger("careerpilot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.data_path.mkdir(parents=True, exist_ok=True)
    settings.backup_dir.mkdir(parents=True, exist_ok=True)
    settings.documents_dir.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)

    init_engine()
    try:
        run_migrations()
        logger.info("Database migrations applied.")
    except Exception as exc:
        logger.error("Migration failed: %s", exc)
        raise

    recovered = task_manager.recover_interrupted()
    if recovered:
        logger.info("Marked %d interrupted tasks as failed.", recovered)

    task_scheduler.start_scheduler()
    logger.info("CareerPilot AI backend started on %s:%s", settings.host, settings.port)

    yield

    task_scheduler.stop_scheduler()


app = FastAPI(
    title="CareerPilot AI",
    version="0.1.0",
    description="Local-first AI career agent backend.",
    docs_url="/docs",
    redoc_url=None,
    lifespan=lifespan,
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_size_limit(request: Request, call_next):
    limit = get_settings().request_max_bytes
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit():
        if int(content_length) > limit:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body too large."},
            )
    response = await call_next(request)
    return response


@app.middleware("http")
async def sanitize_errors(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        logger.exception("Unhandled error on %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred. Check the server logs."},
        )


# Routers
from app.api import (  # noqa: E402
    applications,
    ai_providers,
    documents,
    health,
    insights,
    interviews,
    jobs,
    onboarding,
    privacy,
    settings as settings_router,
    studio,
    tasks,
)

app.include_router(health.router)
app.include_router(onboarding.router)
app.include_router(jobs.router)
app.include_router(documents.router)
app.include_router(applications.router)
app.include_router(interviews.router)
app.include_router(insights.router)
app.include_router(ai_providers.router)
app.include_router(tasks.router)
app.include_router(settings_router.router)
app.include_router(privacy.router)
app.include_router(studio.router)


@app.get("/api/v1")
def api_root():
    return {
        "product": "CareerPilot AI",
        "version": settings.app_version,
        "api": "v1",
        "auth_required": settings.api_require_auth,
    }
