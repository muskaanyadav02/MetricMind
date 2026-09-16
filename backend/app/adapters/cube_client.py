"""Cube.dev adapter placeholder.

Cube is **not implemented in this repository**. In Stage 1 inspection, ``cube/``
was found to contain only a ``README.md`` - there is no ``cube.js``, no model
YAML, no ``package.json`` and no ``docker-compose``. The semantic layer that
``docs/architecture.md`` places between dbt and the AI agent does not exist yet.

This class exists so the swap is a configuration change rather than a rewrite:

* It implements the same :class:`~app.adapters.warehouse.WarehouseAdapter`
  interface as the Snowflake adapter, and returns the same
  :class:`~app.adapters.warehouse.QueryResult`.
* Routes and services depend on the interface, so selecting Cube with
  ``WAREHOUSE_BACKEND=cube`` requires no route changes.

It deliberately does **not** fabricate results. Until a Cube deployment exists,
:meth:`CubeWarehouseAdapter.execute` raises a clear 503 configuration error
explaining exactly what is missing, rather than returning placeholder data.

The intended implementation, once Cube exists, is a POST to Cube's
``/cubejs-api/v1/load`` endpoint with the governed payload already carried by
:class:`~app.schemas.semantic.GovernedQuery` (measures / dimensions / filters /
timeDimensions), which is the same shape ``MetricValidator`` validates.
"""

from __future__ import annotations

from typing import List

from app.adapters.warehouse import QueryPlan, QueryResult, WarehouseAdapter
from app.config import Settings
from app.core.errors import ConfigurationError
from app.core.logging import get_logger

logger = get_logger(__name__)


class CubeWarehouseAdapter(WarehouseAdapter):
    """Not-yet-implemented Cube.dev backend.

    Always refuses to run, with an actionable message. It never returns invented
    data.
    """

    name = "cube"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def is_configured(self) -> bool:
        """Cube always reports unconfigured, because the service does not exist."""
        return False

    def missing_settings(self) -> List[str]:
        return [
            "CUBE_DEPLOYMENT (the Cube.dev semantic layer is not implemented in this repository)"
        ]

    def execute(self, plan: QueryPlan, timeout_seconds: float) -> QueryResult:
        raise ConfigurationError(
            "The Cube.dev semantic layer is not implemented in this repository, so the "
            "'cube' warehouse backend cannot serve queries. "
            "Set WAREHOUSE_BACKEND=snowflake to query the dbt MART models directly. "
            "This adapter exists so Cube can be added later without changing API routes."
        )


__all__ = ["CubeWarehouseAdapter"]
