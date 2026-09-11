"""FastAPI application entry point.

Run locally with::

    uvicorn app.main:app --reload --port 8000

Import safety: this module never connects to Snowflake and never requires
credentials. Importing the app on a machine with no warehouse access is
supported and is what the test suite relies on.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

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
from app.schemas.common import HealthResponse

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

    # CORS for local frontend development. Origins are configuration, not a
    # wildcard: the frontend framework is not yet chosen in this repository, so
    # hardcoding an origin would be a guess and "*" would be unsafe alongside
    # credentials.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def _correlation_id_middleware(request: Request, call_next):
        """Attach a correlation id to every request.

        The id is echoed in the ``X-Correlation-ID`` response header and in the
        ``correlation_id`` field of every error envelope, so a user-visible
        failure can be matched to the server log line that holds the full
        (possibly sensitive) exception detail.

        The contextvar is deliberately *not* reset when the request finishes:
        each request runs in its own context copy, so the value cannot leak into
        another request, and leaving it set is what makes it visible to the
        outermost exception handler (which runs after the middleware stack has
        already unwound).
        """
        correlation_id = request.headers.get(CORRELATION_ID_HEADER) or new_correlation_id()
        correlation_id_var.set(correlation_id)
        response = await call_next(request)
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response

    register_exception_handlers(app)

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    # Convenience alias for local development and simple probes.
    app.add_api_route(
        "/health",
        top_level_health,
        methods=["GET"],
        response_model=HealthResponse,
        tags=["health"],
        summary="Alias of /api/v1/health",
    )

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


__all__ = ["app", "create_app", "CORRELATION_ID_HEADER"]
