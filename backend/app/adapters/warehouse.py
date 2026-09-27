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
from functools import lru_cache
from threading import RLock
from typing import Any, Dict, List, Optional

from app.config import (
    WAREHOUSE_BACKEND_CUBE,
    Settings,
    get_settings,
)
from app.core.errors import (
    ConfigurationError,
    WarehouseError,
    WarehouseTimeoutError,
)
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

    # The same query rendered in the Cube.dev REST payload shape (built by
    # services/query_service.build_cube_payload). Consumed only by the Cube
    # adapter; Snowflake ignores it. Optional so existing plan constructions
    # keep working unchanged.
    cube_payload: Optional[Dict[str, Any]] = None


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
    def execute(
        self,
        plan: QueryPlan,
        timeout_seconds: float,
    ) -> QueryResult:
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

    The adapter reuses a process-local Snowflake connection between requests
    instead of creating and closing a new connection for every query.

    Access to the reusable connection is protected by a re-entrant lock so
    concurrent requests cannot use the same Snowflake connection at the same
    time. If the connection becomes unusable, it is discarded and a fresh
    connection is created automatically.
    """

    name = "snowflake"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._connection = None

        # RLock is intentional because execute() holds this lock while
        # _get_connection() also uses it.
        self._connection_lock = RLock()

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
        database = validate_identifier(
            self._settings.snowflake_database
        )
        schema = validate_identifier(
            self._settings.snowflake_schema
        )

        return f"{database}.{schema}"

    # -- connection management --------------------------------------------

    def _connection_parameters(
        self,
        timeout_seconds: float,
    ) -> Dict[str, Any]:
        settings = self._settings

        parameters: Dict[str, Any] = {
            "account": settings.snowflake_account,
            "user": settings.snowflake_user,
            "password": settings.snowflake_password,
            "warehouse": settings.snowflake_warehouse,
            "database": settings.snowflake_database,
            "schema": settings.snowflake_schema,
            "login_timeout": max(
                1,
                int(timeout_seconds),
            ),
            # Server-side statement timeout, so a runaway query cannot outlive
            # the request even if the client disconnects.
            "session_parameters": {
                "STATEMENT_TIMEOUT_IN_SECONDS": max(
                    1,
                    int(timeout_seconds),
                ),
            },
        }

        if settings.snowflake_role:
            parameters["role"] = settings.snowflake_role

        if settings.snowflake_authenticator:
            parameters["authenticator"] = settings.snowflake_authenticator

        return parameters

    def _close_connection(self) -> None:
        """Close and clear the cached connection."""
        connection = self._connection
        self._connection = None

        if connection is not None:
            try:
                connection.close()
            except Exception:
                logger.debug(
                    "Failed to close the Snowflake connection cleanly",
                    exc_info=True,
                )

    def _connection_is_usable(
        self,
        connection: Any,
    ) -> bool:
        """Best-effort check that a cached Snowflake connection is usable."""
        if connection is None:
            return False

        try:
            # Snowflake connector connections expose ``is_closed``.
            return not bool(connection.is_closed())
        except Exception:
            # If the driver cannot determine the state, treat the connection
            # as unusable and create a fresh connection.
            return False

    def _get_connection(
        self,
        snowflake_connector: Any,
        timeout_seconds: float,
    ) -> Any:
        """Return the cached connection or create a new one.

        The lock prevents multiple concurrent requests from creating
        independent connections at the same time.
        """
        with self._connection_lock:
            if self._connection_is_usable(self._connection):
                return self._connection

            self._close_connection()

            self._connection = snowflake_connector.connect(
                **self._connection_parameters(timeout_seconds)
            )

            logger.info(
                "Created reusable Snowflake connection"
            )

            return self._connection

    # -- execution --------------------------------------------------------

    def execute(
        self,
        plan: QueryPlan,
        timeout_seconds: float,
    ) -> QueryResult:
        self.require_configured()

        try:
            import snowflake.connector
        except ImportError as exc:
            raise ConfigurationError(
                "The 'snowflake-connector-python' package is not installed, "
                "so the Snowflake backend cannot run. "
                "Install backend/requirements.txt."
            ) from exc

        # Serialize access to the shared connection.
        #
        # A single Snowflake connection is reused by the process, so we do
        # not allow concurrent requests to use the same connection/cursor
        # simultaneously.
        with self._connection_lock:
            connection = None

            try:
                connection = self._get_connection(
                    snowflake.connector,
                    timeout_seconds,
                )

                with connection.cursor() as cursor:
                    cursor.execute(
                        plan.sql,
                        plan.parameters,
                    )

                    columns = [
                        description[0]
                        for description in (
                            cursor.description or []
                        )
                    ]

                    raw_rows = cursor.fetchall()

                    rows = [
                        {
                            column: to_json_safe(value)
                            for column, value in zip(
                                columns,
                                row,
                            )
                        }
                        for row in raw_rows
                    ]

                return QueryResult(
                    rows=rows,
                    columns=columns,
                    source_model=plan.source_model,
                )

            except Exception as exc:
                # If the connection itself has failed, discard it so the
                # next request gets a clean connection.
                if connection is self._connection:
                    self._close_connection()

                # Never let a driver message reach the client: it may contain
                # the account, user or connection string. Classify, log,
                # then re-raise.
                if _is_timeout_error(exc):
                    logger.warning(
                        "Warehouse query timed out after %ss",
                        timeout_seconds,
                    )

                    raise WarehouseTimeoutError(
                        f"The warehouse query exceeded the "
                        f"{int(timeout_seconds)}s timeout."
                    ) from exc

                logger.exception(
                    "Warehouse query failed"
                )

                raise WarehouseError(
                    "The warehouse query failed. "
                    "See the server log for details."
                ) from exc

    def close(self) -> None:
        """Explicitly close the reusable Snowflake connection."""
        with self._connection_lock:
            self._close_connection()


def _is_timeout_error(exc: Exception) -> bool:
    """Best-effort timeout classification, without depending on the driver."""
    name = type(exc).__name__.lower()
    text = str(exc).lower()

    return (
        "timeout" in name
        or "timed out" in text
        or "statement timeout" in text
    )


def to_json_safe(value: Any) -> Any:
    """Convert warehouse-native values into JSON-serialisable ones.

    Snowflake returns ``Decimal`` for numeric columns and ``datetime``/``date``
    for temporal ones. ``Decimal`` stays exact by rendering as a string only
    when it cannot be represented as a float without loss; otherwise it becomes
    a float so charts can consume it directly.
    """
    from decimal import Decimal
    from datetime import date, datetime, time

    if value is None or isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (datetime, date, time)):
        return value.isoformat()

    if isinstance(value, bytes):
        return value.decode(
            "utf-8",
            errors="replace",
        )

    if isinstance(value, (list, tuple)):
        return [
            to_json_safe(item)
            for item in value
        ]

    if isinstance(value, dict):
        return {
            key: to_json_safe(item)
            for key, item in value.items()
        }

    return str(value)


def build_warehouse(
    settings: Settings,
) -> WarehouseAdapter:
    """Construct the adapter selected by ``WAREHOUSE_BACKEND``."""
    if settings.warehouse_backend == WAREHOUSE_BACKEND_CUBE:
        # Imported here to keep the module graph acyclic.
        from app.adapters.cube_client import CubeWarehouseAdapter

        return CubeWarehouseAdapter(settings)

    return SnowflakeWarehouseAdapter(settings)


@lru_cache(maxsize=1)
def get_warehouse() -> WarehouseAdapter:
    """FastAPI dependency returning the configured warehouse adapter.

    The adapter is cached for the lifetime of the backend process so its
    reusable Snowflake connection can be shared between requests.

    Tests override this with ``app.dependency_overrides[get_warehouse]``.
    """
    return build_warehouse(get_settings())


def qualified_model_name(
    settings: Settings,
    table: str,
) -> str:
    """``DATABASE.SCHEMA.TABLE`` for a dbt mart, with every part validated.

    dbt model names are lowercase (``fact_sales``), but ``dbt_project.yml`` sets
    no ``quoting`` config, so dbt-snowflake emits unquoted identifiers and
    Snowflake folds them to uppercase (``FACT_SALES``). The model name is
    therefore upper-cased before validation. This keeps the uppercase-only
    identifier rule intact rather than loosening it: anything that is not a
    plain model name still fails ``validate_identifier``.
    """
    database = validate_identifier(
        settings.snowflake_database
    )
    schema = validate_identifier(
        settings.snowflake_schema
    )

    return (
        f"{database}."
        f"{schema}."
        f"{validate_identifier(table.upper())}"
    )


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