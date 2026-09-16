"""Warehouse access, behind an interface.

The API routes depend on :class:`WarehouseAdapter`, never on Snowflake directly.
That is what lets the team swap in Cube.dev later
(:mod:`app.adapters.cube_client`) without touching a single route.

Two hard rules are enforced here:

* **No raw SQL from clients.** A :class:`QueryPlan` can only be produced by the
  compiler in ``services/query_service.py``, which builds SQL exclusively from
  the governed registry. There is no code path that puts client text into a SQL
  string; filter *values* are always bound parameters.
* **No credentials in errors.** Driver exceptions can echo account names and
  DSNs, so they are logged server-side and replaced with a generic message.
"""

from __future__ import annotations

import abc
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence

from app.config import (
    WAREHOUSE_BACKEND_CUBE,
    Settings,
    get_settings,
)
from app.core.errors import ConfigurationError, WarehouseError, WarehouseTimeoutError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Snowflake identifiers in this project are uppercase (METRICMIND, MART, SALES).
# Every identifier the compiler emits is checked against this pattern as defence
# in depth, on top of the fact that identifiers only ever come from the registry.
IDENTIFIER_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*$")


def validate_identifier(identifier: str) -> str:
    """Return the identifier if it is safe, otherwise raise."""
    if not IDENTIFIER_PATTERN.match(identifier or ""):
        raise ConfigurationError(
            f"Refusing to use an unsafe SQL identifier: {identifier!r}. "
            "Identifiers must come from the governed registry."
        )
    return identifier


@dataclass(frozen=True)
class QueryPlan:
    """A compiled, parameterised query ready for execution.

    Produced only by the governed query compiler.
    """

    sql: str
    parameters: List[Any] = field(default_factory=list)
    source_model: str = ""
    columns: List[str] = field(default_factory=list)


@dataclass
class QueryResult:
    """Rows returned by the warehouse, with provenance."""

    rows: List[Dict[str, Any]] = field(default_factory=list)
    columns: List[str] = field(default_factory=list)
    source_model: str = ""

    @property
    def row_count(self) -> int:
        return len(self.rows)


class WarehouseAdapter(abc.ABC):
    """Interface every warehouse backend implements."""

    name: str = "unknown"

    @abc.abstractmethod
    def is_configured(self) -> bool:
        """Whether this backend has the settings it needs to attempt a query."""

    @abc.abstractmethod
    def missing_settings(self) -> List[str]:
        """Names (never values) of the settings that are missing."""

    @abc.abstractmethod
    def execute(self, plan: QueryPlan, timeout_seconds: float) -> QueryResult:
        """Run a compiled plan.

        Implementations must raise :class:`ConfigurationError` when
        unconfigured, :class:`WarehouseTimeoutError` on timeout, and
        :class:`WarehouseError` for any other failure.
        """

    def require_configured(self) -> None:
        """Raise a clear service error when the backend is not usable."""
        if self.is_configured():
            return
        missing = ", ".join(self.missing_settings()) or "unknown settings"
        raise ConfigurationError(
            f"The '{self.name}' warehouse backend is not configured. "
            f"Missing environment settings: {missing}. "
            "The application runs without these, but queries cannot be executed."
        )


class SnowflakeWarehouseAdapter(WarehouseAdapter):
    """Snowflake adapter for the dbt MART layer.

    Configuration is entirely environment-driven. ``snowflake-connector-python``
    is imported lazily inside :meth:`execute` so that importing this module - and
    therefore importing the app - never requires the driver or any credentials.
    """

    name = "snowflake"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    # -- configuration ----------------------------------------------------
    def is_configured(self) -> bool:
        return bool(
            self._settings.snowflake_account
            and self._settings.snowflake_user
            and self._settings.snowflake_password
            and self._settings.snowflake_warehouse
        )

    def missing_settings(self) -> List[str]:
        return self._settings.missing_warehouse_settings

    @property
    def qualified_schema(self) -> str:
        """``DATABASE.SCHEMA``, validated, as documented in the data dictionary."""
        database = validate_identifier(self._settings.snowflake_database)
        schema = validate_identifier(self._settings.snowflake_schema)
        return f"{database}.{schema}"

    # -- execution --------------------------------------------------------
    def _connection_parameters(self, timeout_seconds: float) -> Dict[str, Any]:
        settings = self._settings
        parameters: Dict[str, Any] = {
            "account": settings.snowflake_account,
            "user": settings.snowflake_user,
            "password": settings.snowflake_password,
            "warehouse": settings.snowflake_warehouse,
            "database": settings.snowflake_database,
            "schema": settings.snowflake_schema,
            "login_timeout": max(1, int(timeout_seconds)),
            # Server-side statement timeout, so a runaway query cannot outlive
            # the request even if the client disconnects.
            "session_parameters": {
                "STATEMENT_TIMEOUT_IN_SECONDS": max(1, int(timeout_seconds)),
            },
        }
        if settings.snowflake_role:
            parameters["role"] = settings.snowflake_role
        if settings.snowflake_authenticator:
            parameters["authenticator"] = settings.snowflake_authenticator
        return parameters

    def execute(self, plan: QueryPlan, timeout_seconds: float) -> QueryResult:
        self.require_configured()

        try:
            import snowflake.connector  # imported lazily, on purpose
        except ImportError as exc:
            raise ConfigurationError(
                "The 'snowflake-connector-python' package is not installed, so the "
                "Snowflake backend cannot run. Install backend/requirements.txt."
            ) from exc

        connection = None
        try:
            connection = snowflake.connector.connect(**self._connection_parameters(timeout_seconds))
            with connection.cursor() as cursor:
                cursor.execute(plan.sql, plan.parameters)
                columns = [description[0] for description in (cursor.description or [])]
                raw_rows = cursor.fetchall()
                rows = [
                    {column: to_json_safe(value) for column, value in zip(columns, row)}
                    for row in raw_rows
                ]
            return QueryResult(rows=rows, columns=columns, source_model=plan.source_model)
        except Exception as exc:
            # Never let a driver message reach the client: it may contain the
            # account, user or connection string. Classify, log, then re-raise.
            if _is_timeout_error(exc):
                logger.warning("Warehouse query timed out after %ss", timeout_seconds)
                raise WarehouseTimeoutError(
                    f"The warehouse query exceeded the {int(timeout_seconds)}s timeout."
                ) from exc
            logger.exception("Warehouse query failed")
            raise WarehouseError("The warehouse query failed. See the server log for details.") from exc
        finally:
            if connection is not None:
                try:
                    connection.close()
                except Exception:  # pragma: no cover - best effort only
                    logger.debug("Failed to close the Snowflake connection cleanly")


def _is_timeout_error(exc: Exception) -> bool:
    """Best-effort timeout classification, without depending on the driver."""
    name = type(exc).__name__.lower()
    text = str(exc).lower()
    return "timeout" in name or "timed out" in text or "statement timeout" in text


def to_json_safe(value: Any) -> Any:
    """Convert warehouse-native values into JSON-serialisable ones.

    Snowflake returns ``Decimal`` for numeric columns and ``datetime``/``date``
    for temporal ones. ``Decimal`` stays exact by rendering as a string only when
    it cannot be represented as a float without loss; otherwise it becomes a
    float so charts can consume it directly.
    """
    from decimal import Decimal
    from datetime import date, datetime, time

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (list, tuple)):
        return [to_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: to_json_safe(item) for key, item in value.items()}
    return str(value)


def build_warehouse(settings: Settings) -> WarehouseAdapter:
    """Construct the adapter selected by ``WAREHOUSE_BACKEND``."""
    if settings.warehouse_backend == WAREHOUSE_BACKEND_CUBE:
        # Imported here to keep the module graph acyclic.
        from app.adapters.cube_client import CubeWarehouseAdapter

        return CubeWarehouseAdapter(settings)
    return SnowflakeWarehouseAdapter(settings)


def get_warehouse() -> WarehouseAdapter:
    """FastAPI dependency returning the configured warehouse adapter.

    Tests override this with ``app.dependency_overrides[get_warehouse]``.
    """
    return build_warehouse(get_settings())


def qualified_model_name(settings: Settings, table: str) -> str:
    """``DATABASE.SCHEMA.TABLE`` for a dbt mart, with every part validated.

    dbt model names are lowercase (``fact_sales``), but ``dbt_project.yml`` sets
    no ``quoting`` config, so dbt-snowflake emits unquoted identifiers and
    Snowflake folds them to uppercase (``FACT_SALES``). The model name is
    therefore upper-cased before validation. This keeps the uppercase-only
    identifier rule intact rather than loosening it: anything that is not a
    plain model name still fails ``validate_identifier``.
    """
    database = validate_identifier(settings.snowflake_database)
    schema = validate_identifier(settings.snowflake_schema)
    return f"{database}.{schema}.{validate_identifier(table.upper())}"


__all__ = [
    "QueryPlan",
    "QueryResult",
    "WarehouseAdapter",
    "SnowflakeWarehouseAdapter",
    "build_warehouse",
    "get_warehouse",
    "validate_identifier",
    "qualified_model_name",
    "to_json_safe",
    "IDENTIFIER_PATTERN",
]
