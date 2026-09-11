"""Logging setup and request correlation ids.

A correlation id is attached to every request and echoed in error responses, so
a user-facing failure can be traced to the server-side log line that carries the
real (possibly sensitive) exception detail.
"""

from __future__ import annotations

import contextvars
import logging
import sys
import uuid

correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default=""
)

_LOG_FORMAT = "%(asctime)s %(levelname)-8s [%(name)s] %(message)s"


def get_logger(name: str) -> logging.Logger:
    """Return a module logger."""
    return logging.getLogger(name)


def new_correlation_id() -> str:
    """Generate a short correlation id."""
    return uuid.uuid4().hex[:12]


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging once, for both local runs and uvicorn."""
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level)
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root.addHandler(handler)
    root.setLevel(level)


__all__ = ["correlation_id_var", "get_logger", "new_correlation_id", "configure_logging"]
