"""
app/main.py — FastAPI application factory and lifespan manager.

Responsibilities:
  - Create the FastAPI instance with metadata
  - Register CORS middleware
  - Register global exception handlers
  - Mount API routers
  - Manage startup/shutdown lifecycle (DB, Qdrant, graph)

Architecture Rule: No business logic here.
                   No direct DB calls here.
                   main.py is purely wiring and configuration.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.logging_config import setup_logging

# ── Import after logging_config so loggers work immediately ──────────────────
settings = get_settings()

# Setup logging first — before any other imports that might log
setup_logging(
    log_level=settings.effective_log_level,
    json_output=settings.is_production,     # JSON in production, plain in dev
)

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────────────────
# Lifespan — startup / shutdown
# ────────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    Code before `yield` runs on startup; code after runs on shutdown.

    Startup sequence:
      1. Initialise database engine & create tables
      2. Connect to Qdrant
      3. Build LangGraph skeleton
      4. Log ready state

    Shutdown sequence:
      1. Disconnect Qdrant
      2. Dispose DB engine pool
    """
    # ── STARTUP ──────────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info(f"Starting {settings.APP_NAME}")
    logger.info(f"Environment : {settings.APP_ENV}")
    logger.info(f"Debug mode  : {settings.DEBUG}")
    logger.info("=" * 60)

    # 1. Database
    try:
        from db.session import init_db
        await init_db()
    except Exception as exc:
        logger.critical("Database initialisation failed", extra={"error": str(exc)})
        raise

    # 2. Qdrant
    try:
        from vector_store.qdrant_client import qdrant_wrapper
        await qdrant_wrapper.connect()
        if not qdrant_wrapper.is_healthy:
            logger.warning(
                "Qdrant is reachable but health check returned unhealthy — "
                "check credentials and cluster status"
            )
    except Exception as exc:
        # Non-fatal in Phase 0 — log and continue
        logger.warning("Qdrant connection failed (non-fatal in Phase 0)", extra={"error": str(exc)})

    # 3. LangGraph
    try:
        from agent.graph import financial_graph  # noqa: F401
        logger.info("LangGraph agent graph loaded")
    except Exception as exc:
        logger.warning("LangGraph initialisation failed", extra={"error": str(exc)})

    logger.info(f"{settings.APP_NAME} is ready ✓ — listening on {settings.HOST}:{settings.PORT}")

    # Phase 16: Cold-start pre-warming (cache init + demo preload + health checks)
    try:
        from utils.demo_mode import run_cold_start_tasks
        await run_cold_start_tasks()
    except Exception as exc:
        logger.warning("Cold-start tasks failed (non-fatal): %s", exc)

    yield  # ── Application is running ─────────────────────────────────────────

    # ── SHUTDOWN ─────────────────────────────────────────────────────────────
    logger.info("Shutting down...")

    try:
        from vector_store.qdrant_client import qdrant_wrapper
        await qdrant_wrapper.disconnect()
    except Exception as exc:
        logger.warning("Error disconnecting Qdrant", extra={"error": str(exc)})

    try:
        from db.session import close_db
        await close_db()
    except Exception as exc:
        logger.warning("Error closing DB", extra={"error": str(exc)})

    logger.info("Shutdown complete")


# ────────────────────────────────────────────────────────────────────────────
# Application factory
# ────────────────────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Using a factory function (rather than a module-level instance) makes
    the app easy to test — each test can call create_app() to get a fresh instance.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "Production-grade financial research agent. "
            "Combines LLM reasoning, real-time market data, and vector memory."
        ),
        version="0.16.0",               # Phase 16 — Performance Optimization & Demo Mode
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    # TODO: Restrict `allow_origins` to your frontend domain in production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # Allow all origins temporarily so Render frontend can connect
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Phase 16: Request timing middleware
    from utils.performance import RequestTimingMiddleware
    app.add_middleware(RequestTimingMiddleware)

    # ── Exception handlers ───────────────────────────────────────────────────
    _register_exception_handlers(app)

    # ── Routers ──────────────────────────────────────────────────────────────
    _register_routers(app)

    return app


# ────────────────────────────────────────────────────────────────────────────
# Exception handlers
# ────────────────────────────────────────────────────────────────────────────
def _register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers that return structured JSON errors."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic v2 request validation failures (422)."""
        # Ensure errors are JSON serializable (Pydantic v2 can include bytes)
        errors = exc.errors()
        for error in errors:
            if "input" in error and isinstance(error["input"], bytes):
                error["input"] = str(error["input"])

        logger.warning(
            "Request validation error",
            extra={"path": str(request.url), "errors": errors},
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": "Validation error",
                "detail": errors,
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Catch-all for unhandled exceptions — prevents leaking tracebacks."""
        logger.error(
            "Unhandled exception",
            exc_info=exc,
            extra={"path": str(request.url), "method": request.method},
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "Internal server error",
                "detail": str(exc) if settings.is_debug else "An unexpected error occurred.",
            },
        )


# ────────────────────────────────────────────────────────────────────────────
# Router registration
# ────────────────────────────────────────────────────────────────────────────
def _register_routers(app: FastAPI) -> None:
    """Mount all API routers. Add new routers here as phases progress."""
    from api.routes.health import router as health_router
    from api.routes.auth import router as auth_router
    from api.routes.preferences import router as preferences_router
    from api.routes.market import router as market_router
    from api.routes.forecast import router as forecast_router
    from api.routes.fundamentals import router as fundamentals_router
    from api.routes.risk import router as risk_router
    from api.routes.scenario import router as scenario_router
    from api.routes.compare import router as compare_router
    from api.routes.agent import router as agent_router
    from api.routes.insights import router as insights_router
    from api.routes.confidence import router as confidence_router
    from api.routes.memory import router as memory_router
    from api.routes.chat import router as chat_router
    from api.routes.recommendations import router as recommendations_router
    from api.routes.demo import router as demo_router
    from api.routes.metrics import router as metrics_router
    from api.routes.search import router as search_router
    from api.routes.ai_insights import router as ai_insights_router

    # Phase 0: health at root (no prefix)
    app.include_router(health_router)

    # Phase 1 -> 9: versioned routers at /api/v1
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(preferences_router, prefix="/api/v1")
    app.include_router(market_router, prefix="/api/v1")
    app.include_router(forecast_router, prefix="/api/v1")
    app.include_router(fundamentals_router, prefix="/api/v1")
    app.include_router(risk_router, prefix="/api/v1")
    app.include_router(scenario_router, prefix="/api/v1")
    app.include_router(compare_router, prefix="/api/v1")
    app.include_router(agent_router, prefix="/api/v1")

    # Phase 10: Insight Synthesis
    app.include_router(insights_router, prefix="/api/v1")

    # Phase 11: Confidence & Transparency
    app.include_router(confidence_router, prefix="/api/v1")

    # Phase 12: Qdrant Semantic Memory
    app.include_router(memory_router, prefix="/api/v1")

    # Phase 13: LLM Integration Layer
    app.include_router(chat_router, prefix="/api/v1")

    # Phase 15: Personalization & Smart Recommendations
    app.include_router(recommendations_router, prefix="/api/v1")

    # Phase 16: Demo Mode
    app.include_router(demo_router, prefix="/api/v1")

    # Phase 16: Performance Metrics
    app.include_router(metrics_router, prefix="/api/v1")

    # Feature 1: Company Search
    app.include_router(search_router, prefix="/api/v1")

    # Feature 3: AI Insights
    app.include_router(ai_insights_router, prefix="/api/v1")


# ────────────────────────────────────────────────────────────────────────────
# ASGI entry point
# ────────────────────────────────────────────────────────────────────────────
app: FastAPI = create_app()

# Run with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
