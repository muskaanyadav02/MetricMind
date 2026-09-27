"""FastAPI application entry point.

Run locally with::

    uvicorn app.main:app --reload --port 8000

Import safety: this module never connects to Snowflake and never requires
credentials. Importing the app on a machine with no warehouse access is
supported and is what the test suite relies on.
"""

from __future__ import annotations

import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.adapters.agent_loader import load_agent_module
from app.adapters.warehouse import get_warehouse
from app.api.v1.router import api_router
from app.api.v1.routes_health import top_level_health
from app.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import (
    configure_logging,
    correlation_id_var,
    get_logger,
    new_correlation_id,
)
from app.schemas.common import ErrorResponse, HealthResponse
from app.services.validation_service import (
    load_data_validation_module,
    load_metric_validation_module,
)

logger = get_logger(__name__)

CORRELATION_ID_HEADER = "X-Correlation-ID"


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Backend for MetricMind, a governed Business Intelligence platform. "
            "Questions are answered through governed metrics and dimensions only; "
            "the API accepts no raw SQL."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ------------------------------------------------------------------
    # Startup warm-up
    # ------------------------------------------------------------------

    @app.on_event("startup")
    async def warmup_application() -> None:
        """Warm lazy components before serving user requests.

        The AI agent and validation modules are cached internally. Loading
        them during startup prevents the first chat request from paying their
        import/initialisation cost.
        """
        warmup_start = time.perf_counter()

        # --------------------------------------------------------------
        # 1. Warm the local AI agent
        # --------------------------------------------------------------
        agent_start = time.perf_counter()

        try:
            load_agent_module()

            logger.info(
                "AI agent warm-up completed in %.3f seconds",
                time.perf_counter() - agent_start,
            )

        except Exception:
            logger.exception(
                "AI agent warm-up failed; continuing without warm-up."
            )

        # --------------------------------------------------------------
        # 2. Warm the validation modules
        # --------------------------------------------------------------
        validation_start = time.perf_counter()

        try:
            load_metric_validation_module()
            load_data_validation_module()

            logger.info(
                "Validation warm-up completed in %.3f seconds",
                time.perf_counter() - validation_start,
            )

        except Exception:
            logger.exception(
                "Validation warm-up failed; continuing without warm-up."
            )

        logger.info(
            "Application warm-up completed in %.3f seconds",
            time.perf_counter() - warmup_start,
        )

    # ------------------------------------------------------------------
    # Shutdown cleanup
    # ------------------------------------------------------------------

    @app.on_event("shutdown")
    async def shutdown_application() -> None:
        """Close the reusable warehouse connection during application shutdown."""
        try:
            warehouse = get_warehouse()

            close_method = getattr(warehouse, "close", None)

            if callable(close_method):
                close_method()

                logger.info(
                    "Warehouse connection cleanup completed."
                )

        except Exception:
            logger.exception(
                "Warehouse connection cleanup failed during shutdown."
            )

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # Correlation ID middleware
    # ------------------------------------------------------------------

    @app.middleware("http")
    async def _correlation_id_middleware(
        request: Request,
        call_next,
    ):
        """Attach a correlation id to every request."""
        correlation_id = (
            request.headers.get(CORRELATION_ID_HEADER)
            or new_correlation_id()
        )

        correlation_id_var.set(correlation_id)

        response = await call_next(request)

        response.headers[CORRELATION_ID_HEADER] = correlation_id

        return response

    # ------------------------------------------------------------------
    # Exception handlers
    # ------------------------------------------------------------------

    register_exception_handlers(app)

    # ------------------------------------------------------------------
    # API routes
    # ------------------------------------------------------------------

    app.include_router(
        api_router,
        prefix=settings.api_v1_prefix,
    )

    app.add_api_route(
        "/health",
        top_level_health,
        methods=["GET"],
        response_model=HealthResponse,
        tags=["health"],
        summary="Alias of /api/v1/health",
        responses={
            200: {
                "description": (
                    "Service status summary. 'ok' when all dependencies "
                    "are usable, 'degraded' otherwise."
                ),
            },
            500: {
                "model": ErrorResponse,
                "description": (
                    "Unexpected internal error, rendered in the standard "
                    "error envelope (internal_error)."
                ),
            },
        },
    )

    # ------------------------------------------------------------------
    # Root endpoint
    # ------------------------------------------------------------------

    @app.get("/", include_in_schema=False)
    def root() -> dict:
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/api/v1/health",
            "api": settings.api_v1_prefix,
        }

    logger.info(
        "%s v%s initialised (warehouse backend=%s, configured=%s)",
        settings.app_name,
        settings.app_version,
        settings.warehouse_backend,
        settings.warehouse_configured,
    )

    return app


app = create_app()


__all__ = [
    "app",
    "create_app",
    "CORRELATION_ID_HEADER",
]