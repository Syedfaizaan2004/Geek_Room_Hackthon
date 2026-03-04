"""
api/routes/health.py — System health & root endpoints.

GET /          → System metadata (app info, version, environment)
GET /health    → Deep health check (DB + Qdrant connectivity)

No business logic lives here — all checks delegate to the
init functions wired up in main.py lifespan.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import get_settings
from db.session import AsyncSessionFactory
from vector_store.qdrant_client import qdrant_wrapper

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["Health"])

# Application version — bump manually or wire to git tag in CI
APP_VERSION = "0.1.0"


@router.get(
    "/",
    summary="Root — System metadata",
    response_description="Application name, version, and environment",
)
async def root() -> dict[str, Any]:
    """
    Root endpoint.
    Returns lightweight system metadata without performing any I/O checks.
    Useful for quick sanity checks and load-balancer pings.
    """
    return {
        "app": settings.APP_NAME,
        "version": APP_VERSION,
        "environment": settings.APP_ENV,
        "docs": "/docs",
        "health": "/health",
        "status": "online",
    }


@router.get(
    "/health",
    summary="Deep health check",
    response_description="Status of all infrastructure components",
)
async def health_check(request: Request) -> JSONResponse:
    """
    Deep health check endpoint.

    Checks:
      1. Database connectivity — executes a lightweight SELECT 1
      2. Qdrant connectivity  — pings the configured cluster

    Returns HTTP 200 if all checks pass, HTTP 503 if any fail.
    The response body always contains per-component status.
    """
    start_time = time.perf_counter()
    results: dict[str, Any] = {
        "app": settings.APP_NAME,
        "version": APP_VERSION,
        "environment": settings.APP_ENV,
        "components": {},
    }

    # ── 1. Database check ────────────────────────────────────────────────────
    db_ok = False
    try:
        async with AsyncSessionFactory() as session:
            await session.execute(text("SELECT 1"))
        db_ok = True
        logger.debug("Health check: DB OK")
    except Exception as exc:
        logger.warning("Health check: DB FAILED", extra={"error": str(exc)})

    results["components"]["database"] = {
        "status": "healthy" if db_ok else "unhealthy",
        "type": "sqlite" if "sqlite" in settings.DATABASE_URL else "postgresql",
    }

    # ── 2. Qdrant check ──────────────────────────────────────────────────────
    qdrant_ok = await qdrant_wrapper.health_check()
    logger.debug("Health check: Qdrant %s", "OK" if qdrant_ok else "FAILED")

    results["components"]["qdrant"] = {
        "status": "healthy" if qdrant_ok else "unhealthy",
        "collection": settings.QDRANT_COLLECTION,
    }

    # ── Aggregate status ─────────────────────────────────────────────────────
    all_healthy = db_ok and qdrant_ok
    results["status"] = "healthy" if all_healthy else "degraded"
    results["latency_ms"] = round((time.perf_counter() - start_time) * 1000, 2)

    http_status = 200 if all_healthy else 503
    return JSONResponse(content=results, status_code=http_status)
