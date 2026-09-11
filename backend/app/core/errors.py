"""Error types and the single, consistent API error response format.

Every failure that reaches a client - whether raised by our own code, by a
Pydantic request model, or by an unexpected exception - is rendered by
:func:`register_exception_handlers` into the same JSON envelope::

    {"error": {"code": "...", "message": "...", "details": [...], "correlation_id": "..."}}

Two rules matter for security:

* Upstream driver messages are never copied into a response. A Snowflake
  connection error can echo the account, user or DSN, so the full exception is
  logged server-side and the client receives a generic message plus a
  correlation id.
* The ``message`` on a :class:`MetricMindError` is always authored by us.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import correlation_id_var, get_logger

logger = get_logger(__name__)


class MetricMindError(Exception):
    """Base class for all deliberate, client-safe errors."""

    code: str = "internal_error"
    status_code: int = 500
    default_message: str = "An unexpected error occurred."

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.message = message or self.default_message
        self.details: List[Dict[str, Any]] = list(details or [])
        super().__init__(self.message)


# -- 4xx -----------------------------------------------------------------
class NotFoundError(MetricMindError):
    code = "not_found"
    status_code = 404
    default_message = "The requested resource was not found."


class UnsupportedQuestionError(MetricMindError):
    """The question cannot be turned into a governed query."""

    code = "unsupported_question"
    status_code = 422
    default_message = "The question cannot be answered with the governed metrics and dimensions."


class ValidationFailedError(MetricMindError):
    code = "validation_failed"
    status_code = 422
    default_message = "The governed query failed validation."


class BadRequestError(MetricMindError):
    code = "bad_request"
    status_code = 400
    default_message = "The request was malformed."


# -- 5xx -----------------------------------------------------------------
class ConfigurationError(MetricMindError):
    """The server is missing configuration it needs (e.g. no warehouse creds).

    This is a *service* condition, not the client's fault, so it is reported as
    503 with a message that names the missing settings but never their values.
    """

    code = "configuration_error"
    status_code = 503
    default_message = "The server is not fully configured."


class WarehouseError(MetricMindError):
    code = "warehouse_error"
    status_code = 502
    default_message = "The warehouse query failed."


class WarehouseTimeoutError(MetricMindError):
    code = "warehouse_timeout"
    status_code = 504
    default_message = "The warehouse query timed out."


class AgentError(MetricMindError):
    code = "agent_error"
    status_code = 502
    default_message = "The AI agent could not interpret the question."


class AgentUnavailableError(MetricMindError):
    code = "agent_unavailable"
    status_code = 503
    default_message = "The AI agent module is unavailable."


# -- Rendering -----------------------------------------------------------
def error_body(
    code: str,
    message: str,
    details: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Build the canonical error envelope."""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": list(details or []),
            "correlation_id": correlation_id_var.get(),
        }
    }


def register_exception_handlers(app: FastAPI) -> None:
    """Attach the handlers that produce the canonical error envelope."""

    @app.exception_handler(MetricMindError)
    async def _handle_metricmind_error(request: Request, exc: MetricMindError) -> JSONResponse:
        logger.warning(
            "Handled error %s on %s %s: %s",
            exc.code,
            request.method,
            request.url.path,
            exc.message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_request_validation(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = []
        for error in exc.errors():
            location = ".".join(str(part) for part in error.get("loc", ()) if part != "body")
            details.append(
                {
                    "field": location or "body",
                    "message": error.get("msg", "Invalid value."),
                    "type": error.get("type", "value_error"),
                }
            )
        logger.info("Request validation failed on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=422,
            content=error_body("request_validation_error", "The request payload is invalid.", details),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "HTTP error."
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body("http_error", message),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        # Full detail goes to the server log only. The client gets no internals.
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content=error_body(
                "internal_error",
                "An unexpected internal error occurred. Quote the correlation id when reporting it.",
            ),
        )


__all__ = [
    "MetricMindError",
    "NotFoundError",
    "UnsupportedQuestionError",
    "ValidationFailedError",
    "BadRequestError",
    "ConfigurationError",
    "WarehouseError",
    "WarehouseTimeoutError",
    "AgentError",
    "AgentUnavailableError",
    "error_body",
    "register_exception_handlers",
]
