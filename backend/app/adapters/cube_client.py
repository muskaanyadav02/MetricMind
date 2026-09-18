"""Cube.dev REST adapter.

Implements :class:`~app.adapters.warehouse.WarehouseAdapter` against a Cube
deployment's ``/cubejs-api/v1/load`` endpoint, so ``WAREHOUSE_BACKEND=cube``
serves governed queries from the semantic layer without any route changes.

How a query reaches Cube:

1. The compiler (``services/query_service.py``) attaches the governed payload
   from :func:`app.services.query_service.build_cube_payload` to the
   :class:`~app.adapters.warehouse.QueryPlan` (``plan.cube_payload``). This
   adapter consumes exactly that structure - payload construction is not
   duplicated here.
2. Governed names are translated to Cube member names **from the deployed
   model** (``cube/model/FactSales.js``), and row keys are translated back to
   governed names on the way out, so the rest of the backend (answer
   summarisation, response schemas) works identically over either warehouse.
3. The query is POSTed to ``{CUBE_API_URL}/load``. ``CUBE_API_URL`` comes from
   configuration; nothing about the Cube deployment is hardcoded.
4. Cube returns numbers as *strings* (documented Cube behaviour: "Client code
   should take care of parsing such numerical values"), so numeric-looking
   scalar values are parsed back to ``int``/``float``. Everything else
   (dates, names) is passed through untouched.

Authentication: ``CUBE_API_TOKEN`` is optional. Cube's REST API documents an
``Authorization`` header, but Cube also runs in development mode
(``CUBEJS_DEV_MODE=true``, the default for local ``cubejs``/Docker setups),
which is a documented authentication bypass. The header is therefore sent
*only* when a token is configured, which is correct in both modes. Tokens are
never logged and never included in client-facing error messages.

Error mapping (the same contract as the Snowflake adapter):

* Not configured                          -> ``ConfigurationError`` (503)
* HTTP/connect failure, bad status,       -> ``WarehouseError`` (502)
  malformed body, unmappable member
* Timeout                                 -> ``WarehouseTimeoutError`` (504)

Failures are honest: an unmappable governed member raises before any HTTP call
is made, and no result is ever fabricated when Cube cannot be reached.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.adapters.warehouse import QueryPlan, QueryResult, WarehouseAdapter
from app.config import Settings
from app.core.errors import ConfigurationError, WarehouseError, WarehouseTimeoutError
from app.core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Governed -> Cube member mapping.
#
# Source of truth for the Cube side is the deployed model, cube/model/FactSales.js.
# The governed side is the registry in services/metric_service.py. The two
# vocabularies intentionally differ (governed names are business names such as
# "Quantity Sold"; Cube members are "FactSales.quantitySold"), so the mapping
# is explicit and complete - any governed name missing here refuses loudly
# rather than querying the wrong member.
# ---------------------------------------------------------------------------
CUBE_MODEL_DOC = "cube/model/FactSales.js"

CUBE_METRIC_MEMBERS: Dict[str, str] = {
    "Revenue": "FactSales.revenue",
    "Profit": "FactSales.profit",
    "Profit Margin": "FactSales.profitMargin",
    "Orders": "FactSales.orders",
    "Customers": "FactSales.customers",
    "Quantity Sold": "FactSales.quantitySold",
    "Shipping Cost": "FactSales.shippingCost",
    "Average Order Value": "FactSales.averageOrderValue",
}

CUBE_DIMENSION_MEMBERS: Dict[str, str] = {
    "Country": "FactSales.country",
    "Region": "FactSales.region",
    "Market": "FactSales.market",
    "Market2": "FactSales.market2",
    "City": "FactSales.city",
    "State": "FactSales.state",
    "Ship Mode": "FactSales.shipMode",
    "Order Priority": "FactSales.orderPriority",
}

# Governed time attributes the deployed model can express. FactSales exposes a
# single time member (orderDate), so Year/Quarter/Month/Day are expressible as
# timeDimensions granularities - but not as plain dimensions or filters, which
# is refused rather than silently substituted. Week Number and Month Name have
# no Cube equivalent and are refused outright.
CUBE_TIME_DIMENSION_NAMES = ("Year", "Quarter", "Month", "Day")
CUBE_TIME_MEMBER = "FactSales.orderDate"

# Governed filter operators -> Cube REST API operators. Cube spells set
# membership "equals"/"notEquals" (a set of values is the IN/NOT IN semantics),
# so "in" and "not_in" map there rather than being sent verbatim.
CUBE_FILTER_OPERATORS: Dict[str, str] = {
    "equals": "equals",
    "not_equals": "notEquals",
    "in": "equals",
    "not_in": "notEquals",
    "contains": "contains",
    "gt": "gt",
    "gte": "gte",
    "lt": "lt",
    "lte": "lte",
}

# Cube returns numbers as strings ("700", "12.5"). Only strict numeric shapes
# are parsed - leading zeros ("007", "0042") and anything non-numeric stay
# strings, so identifiers that look numeric are never mangled.
_INT_PATTERN = re.compile(r"^-?(0|[1-9][0-9]*)$")
_FLOAT_PATTERN = re.compile(r"^-?((0|[1-9][0-9]*)(\.[0-9]*)?|\.[0-9]+)([eE][+-]?[0-9]+)?$")


def _coerce_scalar(value: Any) -> Any:
    """Parse Cube's string-encoded numbers; leave every other value untouched."""
    if isinstance(value, str):
        text = value.strip()
        if _INT_PATTERN.match(text):
            return int(text)
        if _FLOAT_PATTERN.match(text):
            return float(text)
    return value


class CubeWarehouseAdapter(WarehouseAdapter):
    """Warehouse adapter for the Cube.dev semantic layer.

    ``transport`` exists for tests only: passing an ``httpx.MockTransport``
    replaces the HTTP layer without any network access. Production code never
    passes it.
    """

    name = "cube"

    def __init__(self, settings: Settings, transport: Optional[httpx.BaseTransport] = None) -> None:
        self._settings = settings
        self._transport = transport

    # -- configuration ------------------------------------------------------
    def is_configured(self) -> bool:
        """The adapter needs only the Cube API URL; the token is optional.

        Local Cube deployments commonly run in development mode
        (``CUBEJS_DEV_MODE=true``), which is a documented authentication
        bypass, so requiring a token would break the standard local setup.
        """
        return bool(self._settings.cube_api_url)

    def missing_settings(self) -> List[str]:
        """Names (never values) of the settings still missing."""
        return [] if self._settings.cube_api_url else ["CUBE_API_URL"]

    # -- payload translation --------------------------------------------------
    def _build_cube_query(self, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """Translate a governed payload into the Cube query and a rename map.

        The rename map takes Cube response keys (``FactSales.revenue``,
        ``FactSales.orderDate.month``, ...) back to governed names. Anything
        the deployed model cannot express is collected and raised *before* any
        HTTP request is made.
        """
        unmappable: List[str] = []
        metric_renames: Dict[str, str] = {}
        dimension_renames: Dict[str, str] = {}
        time_renames: Dict[str, str] = {}

        measures: List[str] = []
        for name in payload.get("measures", []):
            member = CUBE_METRIC_MEMBERS.get(name)
            if member is None:
                unmappable.append(f"metric '{name}'")
                continue
            measures.append(member)
            metric_renames[member] = name

        dimensions: List[str] = []
        for name in payload.get("dimensions", []):
            member = CUBE_DIMENSION_MEMBERS.get(name)
            if member is not None:
                dimensions.append(member)
                dimension_renames[member] = name
            elif name in CUBE_TIME_DIMENSION_NAMES:
                unmappable.append(
                    f"dimension '{name}' (a time attribute; the Cube model only expresses it "
                    f"through '{CUBE_TIME_MEMBER}' granularity in timeDimensions, not as a "
                    "plain dimension or filter)"
                )
            else:
                unmappable.append(f"dimension '{name}'")

        filters: List[Dict[str, Any]] = []
        for governed_filter in payload.get("filters", []):
            name = governed_filter.get("member")
            member = CUBE_DIMENSION_MEMBERS.get(name)
            if member is None:
                if name in CUBE_TIME_DIMENSION_NAMES:
                    unmappable.append(
                        f"filter on '{name}' (a time attribute; the Cube model only expresses it "
                        f"through '{CUBE_TIME_MEMBER}' granularity in timeDimensions, not as a "
                        "plain filter)"
                    )
                else:
                    unmappable.append(f"filter on '{name}'")
                continue
            operator = CUBE_FILTER_OPERATORS.get(governed_filter.get("operator"))
            if operator is None:
                unmappable.append(f"filter operator '{governed_filter.get('operator')}' on '{name}'")
                continue
            filters.append(
                {
                    "member": member,
                    "operator": operator,
                    "values": list(governed_filter.get("values", [])),
                }
            )

        time_dimensions: List[Dict[str, Any]] = []
        for governed_time in payload.get("timeDimensions", []):
            name = governed_time.get("dimension")
            if name in CUBE_TIME_DIMENSION_NAMES:
                key = f"{CUBE_TIME_MEMBER}.{governed_time.get('granularity')}"
                time_dimensions.append(
                    {"dimension": CUBE_TIME_MEMBER, "granularity": governed_time.get("granularity")}
                )
                time_renames[key] = name
            else:
                unmappable.append(f"time dimension '{name}'")

        if unmappable:
            raise WarehouseError(
                f"The governed query references members the deployed Cube model does not "
                f"define ({CUBE_MODEL_DOC} only defines the FactSales cube): "
                + "; ".join(unmappable)
                + ". The query was not sent to Cube."
            )

        rename_map = {**metric_renames, **dimension_renames, **time_renames}
        return (
            {
                "measures": measures,
                "dimensions": dimensions,
                "filters": filters,
                "timeDimensions": time_dimensions,
            },
            rename_map,
        )

    # -- execution ------------------------------------------------------------
    def execute(self, plan: QueryPlan, timeout_seconds: float) -> QueryResult:
        self.require_configured()

        if plan.cube_payload is None:
            raise WarehouseError(
                "The 'cube' backend can only execute plans produced by the governed query "
                "compiler, which attaches the Cube payload. The query was not sent to Cube."
            )

        cube_query, rename_map = self._build_cube_query(plan.cube_payload)
        return self._run_load(cube_query, rename_map, plan, timeout_seconds)

    def _run_load(
        self,
        cube_query: Dict[str, Any],
        rename_map: Dict[str, str],
        plan: QueryPlan,
        timeout_seconds: float,
    ) -> QueryResult:
        url = (self._settings.cube_api_url or "").rstrip("/") + "/load"
        headers = {"Content-Type": "application/json"}
        if self._settings.cube_api_token:
            headers["Authorization"] = self._settings.cube_api_token

        try:
            # transport=None (production) selects httpx's default transport.
            with httpx.Client(timeout=timeout_seconds, transport=self._transport) as client:
                response = client.post(url, json={"query": cube_query}, headers=headers)
        except httpx.TimeoutException as exc:
            logger.warning("Cube request timed out after %ss", timeout_seconds)
            raise WarehouseTimeoutError(
                f"The Cube query exceeded the {int(timeout_seconds)}s timeout."
            ) from exc
        except httpx.HTTPError as exc:
            # Connection failures and protocol errors: Cube's exception text can
            # embed the URL, so it is logged server-side and replaced.
            logger.warning("Cube request failed: %s", exc)
            raise WarehouseError(
                "The Cube service could not be reached. See the server log for details."
            ) from exc

        if response.status_code >= 400:
            # The body may echo configuration; log it server-side, never send it on.
            logger.warning(
                "Cube /load returned HTTP %s: %s",
                response.status_code,
                response.text[:500],
            )
            raise WarehouseError(
                f"The Cube service rejected the query (HTTP {response.status_code}). "
                "See the server log for details."
            )

        try:
            body = response.json()
        except ValueError as exc:
            logger.warning("Cube /load returned a malformed body: %s", exc)
            raise WarehouseError("The Cube service returned a malformed response.") from exc

        data = body.get("data") if isinstance(body, dict) else None
        if not isinstance(data, list):
            raise WarehouseError(
                "The Cube service returned an unexpected response shape (missing 'data')."
            )

        rows: List[Dict[str, Any]] = []
        for item in data:
            if not isinstance(item, dict):
                raise WarehouseError("The Cube service returned an unexpected row shape.")
            rows.append(
                {
                    rename_map.get(key, key): _coerce_scalar(value)
                    for key, value in item.items()
                }
            )

        return QueryResult(rows=rows, columns=list(plan.columns), source_model=plan.source_model)


__all__ = [
    "CubeWarehouseAdapter",
    "CUBE_METRIC_MEMBERS",
    "CUBE_DIMENSION_MEMBERS",
    "CUBE_TIME_DIMENSION_NAMES",
    "CUBE_TIME_MEMBER",
    "CUBE_FILTER_OPERATORS",
]
