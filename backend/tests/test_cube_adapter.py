"""Cube adapter tests.

Every HTTP interaction is mocked with ``httpx.MockTransport`` — no test here
(or anywhere in this suite) needs a running Cube deployment. What is pinned:

* the request Cube receives is derived from the governed query (member mapping,
  operator mapping, timeDimension mapping),
* the response is parsed honestly (keys renamed back to governed names,
  string-encoded numbers parsed),
* authentication matches Cube's documented behaviour (Authorization header
  only when a token is configured — dev-mode Cube needs none),
* every failure mode maps to the backend's existing structured errors
  (ConfigurationError / WarehouseError / WarehouseTimeoutError), and
* the whole chat endpoint works over Cube with zero route changes.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx
import pytest
from fastapi.testclient import TestClient

from app.adapters.cube_client import CubeWarehouseAdapter
from app.adapters.warehouse import QueryPlan, build_warehouse, get_warehouse
from app.config import Settings
from app.core.errors import ConfigurationError, WarehouseError, WarehouseTimeoutError
from app.main import create_app
from app.services.agent_service import AgentService, get_agent_service
from app.services.query_service import build_cube_payload
from tests.conftest import StubAgentAdapter, agent_output

CUBE_URL = "http://cube.test/cubejs-api/v1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_settings(
    url: Optional[str] = CUBE_URL,
    token: Optional[str] = None,
    backend: str = "cube",
) -> Settings:
    return Settings(
        warehouse_backend=backend,
        cube_api_url=url,
        cube_api_token=token,
        snowflake_database="METRICMIND",
        snowflake_schema="MART",
    )


class RecordingTransport(httpx.MockTransport):
    """MockTransport that records requests so tests can assert on the wire format."""

    def __init__(
        self,
        responses: Optional[Dict[str, httpx.Response]] = None,
        exc: Optional[Exception] = None,
    ) -> None:
        super().__init__(self._handler)
        self.requests: List[httpx.Request] = []
        self._responses = responses or {}
        self._exc = exc

    def _handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self._exc is not None:
            raise self._exc
        response = self._responses.get(request.url.path) or self._responses.get("*")
        if response is None:
            return httpx.Response(500, json={"error": "no canned response"})
        return response


def success_response() -> httpx.Response:
    """A /load response in the documented Cube shape (numbers as strings)."""
    return httpx.Response(
        200,
        json={
            "query": {"measures": ["FactSales.revenue"], "dimensions": ["FactSales.country"]},
            "data": [
                {"FactSales.country": "United States", "FactSales.revenue": "12642905.0"},
                {"FactSales.country": "Australia", "FactSales.revenue": "925000.5"},
            ],
            "lastRefreshTime": "2026-09-18T12:00:00.000Z",
            "annotation": {"measures": {}, "dimensions": {}},
        },
    )


def make_adapter(
    transport: Optional[httpx.BaseTransport] = None,
    settings: Optional[Settings] = None,
) -> CubeWarehouseAdapter:
    return CubeWarehouseAdapter(settings or make_settings(), transport=transport)


def make_plan(payload: Optional[Dict[str, Any]] = None) -> QueryPlan:
    """A minimal plan as QueryService.compile() would produce it."""
    return QueryPlan(
        sql="SELECT SUM(f.SALES) AS \"Revenue\" FROM METRICMIND.MART.FACT_SALES AS f LIMIT 100",
        parameters=[],
        source_model="METRICMIND.MART.FACT_SALES",
        columns=["Revenue"],
        cube_payload=payload
        if payload is not None
        else {"measures": ["Revenue"], "dimensions": [], "filters": [], "timeDimensions": []},
    )


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
def test_is_configured_with_url_only() -> None:
    """The URL is the only required setting; the token is optional (dev mode)."""
    adapter = make_adapter(settings=make_settings(url=CUBE_URL, token=None))
    assert adapter.is_configured() is True
    assert adapter.missing_settings() == []


def test_is_configured_without_url() -> None:
    adapter = make_adapter(settings=make_settings(url=None))
    assert adapter.is_configured() is False
    assert adapter.missing_settings() == ["CUBE_API_URL"]


def test_execute_raises_configuration_error_when_unconfigured() -> None:
    adapter = make_adapter(settings=make_settings(url=None))
    with pytest.raises(ConfigurationError) as excinfo:
        adapter.execute(make_plan(), timeout_seconds=10.0)
    # Settings names only — never values.
    assert "CUBE_API_URL" in str(excinfo.value)


def test_build_warehouse_returns_cube_adapter_for_cube_backend() -> None:
    adapter = build_warehouse(make_settings())
    assert isinstance(adapter, CubeWarehouseAdapter)
    assert adapter.name == "cube"


def test_build_warehouse_snowflake_unchanged() -> None:
    """Snowflake selection is untouched by the Cube work."""
    from app.adapters.warehouse import SnowflakeWarehouseAdapter

    adapter = build_warehouse(make_settings(backend="snowflake"))
    assert isinstance(adapter, SnowflakeWarehouseAdapter)


# ---------------------------------------------------------------------------
# Payload derivation from the governed query
# ---------------------------------------------------------------------------
def test_payload_is_built_from_the_governed_query() -> None:
    """The adapter consumes the compiler's plan payload, not its own construction."""
    from app.schemas.semantic import GovernedQuery

    governed = GovernedQuery(measures=["Revenue"], dimensions=["Country"])
    payload = build_cube_payload(governed)
    assert payload == {
        "measures": ["Revenue"],
        "dimensions": ["Country"],
        "filters": [],
        "timeDimensions": [],
    }


def test_request_maps_governed_members_to_cube_members() -> None:
    """The POST body uses FactSales.* members from the deployed Cube model."""
    transport = RecordingTransport({"*": success_response()})
    adapter = make_adapter(transport=transport)
    plan = make_plan(
        {
            "measures": ["Revenue", "Profit"],
            "dimensions": ["Country"],
            "filters": [{"member": "Market", "operator": "in", "values": ["EU"]}],
            "timeDimensions": [],
        }
    )
    result = adapter.execute(plan, timeout_seconds=10.0)
    assert result.row_count == 2

    request = transport.requests[0]
    assert request.method == "POST"
    assert request.url.path == "/cubejs-api/v1/load"
    body = json.loads(request.content)
    assert body == {
        "query": {
            "measures": ["FactSales.revenue", "FactSales.profit"],
            "dimensions": ["FactSales.country"],
            "filters": [
                {"member": "FactSales.market", "operator": "equals", "values": ["EU"]}
            ],
            "timeDimensions": [],
        }
    }


def test_request_reuses_build_cube_payload_output() -> None:
    """plan.cube_payload comes from the existing builder — no duplicated logic."""
    from app.schemas.semantic import GovernedQuery

    governed = GovernedQuery(measures=["Shipping Cost"], dimensions=["Region"])
    payload = build_cube_payload(governed)
    plan = make_plan(payload)

    transport = RecordingTransport({"*": success_response()})
    make_adapter(transport=transport).execute(plan, timeout_seconds=5.0)

    body = json.loads(transport.requests[0].content)
    assert body["query"]["measures"] == ["FactSales.shippingCost"]
    assert body["query"]["dimensions"] == ["FactSales.region"]


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------
def test_response_keys_are_renamed_to_governed_names() -> None:
    adapter = make_adapter(transport=RecordingTransport({"*": success_response()}))
    result = adapter.execute(
        make_plan(
            {
                "measures": ["Revenue"],
                "dimensions": ["Country"],
                "filters": [],
                "timeDimensions": [],
            }
        ),
        timeout_seconds=10.0,
    )

    assert result.columns == ["Revenue"]
    assert result.rows == [
        {"Country": "United States", "Revenue": 12642905.0},
        {"Country": "Australia", "Revenue": 925000.5},
    ]
    assert result.source_model == "METRICMIND.MART.FACT_SALES"


def test_string_encoded_numbers_are_parsed() -> None:
    transport = RecordingTransport(
        {
            "*": httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "FactSales.revenue": "700",
                            "FactSales.profitMargin": "12.5",
                            "FactSales.country": "France",
                            "FactSales.orderId": "0042",
                        }
                    ]
                },
            )
        }
    )
    result = make_adapter(transport=transport).execute(
        make_plan({"measures": ["Revenue"], "dimensions": ["Country"], "filters": [], "timeDimensions": []}),
        timeout_seconds=10.0,
    )

    row = result.rows[0]
    # Queried members are renamed to governed names and their numbers parsed.
    assert row["Revenue"] == 700 and isinstance(row["Revenue"], int)
    # Response keys the query did not ask for stay under their Cube names.
    assert row["FactSales.profitMargin"] == 12.5
    # Leading zeros are identifiers (order ids), not numbers — untouched.
    assert row["FactSales.orderId"] == "0042"
    assert row["Country"] == "France"


def test_time_dimension_mapping_and_rename() -> None:
    transport = RecordingTransport(
        {
            "*": httpx.Response(
                200,
                json={"data": [{"FactSales.orderDate.month": "2026-09", "FactSales.revenue": "10"}]},
            )
        }
    )
    result = make_adapter(transport=transport).execute(
        make_plan(
            {
                "measures": ["Revenue"],
                "dimensions": [],
                "filters": [],
                "timeDimensions": [{"dimension": "Month", "granularity": "month"}],
            }
        ),
        timeout_seconds=10.0,
    )

    body = json.loads(transport.requests[0].content)
    assert body["query"]["timeDimensions"] == [
        {"dimension": "FactSales.orderDate", "granularity": "month"}
    ]
    assert result.rows == [{"Month": "2026-09", "Revenue": 10}]


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
def test_authorization_header_sent_when_token_configured() -> None:
    transport = RecordingTransport({"*": success_response()})
    adapter = make_adapter(
        transport=transport,
        settings=make_settings(url=CUBE_URL, token="test-token-value"),
    )
    adapter.execute(make_plan(), timeout_seconds=10.0)
    assert transport.requests[0].headers["Authorization"] == "test-token-value"


def test_no_authorization_header_without_token() -> None:
    """Dev-mode Cube (documented auth bypass) needs no token."""
    transport = RecordingTransport({"*": success_response()})
    make_adapter(transport=transport).execute(make_plan(), timeout_seconds=10.0)
    assert "Authorization" not in transport.requests[0].headers


# ---------------------------------------------------------------------------
# Failure mapping
# ---------------------------------------------------------------------------
def test_http_500_maps_to_warehouse_error() -> None:
    transport = RecordingTransport(
        {"*": httpx.Response(500, json={"error": "internal cube detail"})}
    )
    with pytest.raises(WarehouseError) as excinfo:
        make_adapter(transport=transport).execute(make_plan(), timeout_seconds=10.0)
    assert "500" in str(excinfo.value)
    assert "internal cube detail" not in str(excinfo.value)


def test_http_400_maps_to_warehouse_error() -> None:
    transport = RecordingTransport({"*": httpx.Response(400, json={"error": "Continue wait"})})
    with pytest.raises(WarehouseError):
        make_adapter(transport=transport).execute(make_plan(), timeout_seconds=10.0)


def test_token_never_leaks_into_client_error() -> None:
    transport = RecordingTransport({"*": httpx.Response(401, json={"error": "invalid token"})})
    adapter = make_adapter(
        transport=transport,
        settings=make_settings(url=CUBE_URL, token="super-secret-token"),
    )
    with pytest.raises(WarehouseError) as excinfo:
        adapter.execute(make_plan(), timeout_seconds=10.0)
    assert "super-secret-token" not in str(excinfo.value)


def test_connect_timeout_maps_to_warehouse_timeout() -> None:
    transport = RecordingTransport(exc=httpx.ConnectTimeout("timed out"))
    with pytest.raises(WarehouseTimeoutError):
        make_adapter(transport=transport).execute(make_plan(), timeout_seconds=10.0)


def test_read_timeout_maps_to_warehouse_timeout() -> None:
    transport = RecordingTransport(exc=httpx.ReadTimeout("timed out"))
    with pytest.raises(WarehouseTimeoutError):
        make_adapter(transport=transport).execute(make_plan(), timeout_seconds=10.0)


def test_connect_error_maps_to_warehouse_error() -> None:
    transport = RecordingTransport(exc=httpx.ConnectError("connection refused"))
    with pytest.raises(WarehouseError):
        make_adapter(transport=transport).execute(make_plan(), timeout_seconds=10.0)


def test_missing_data_key_maps_to_warehouse_error() -> None:
    transport = RecordingTransport({"*": httpx.Response(200, json={"unexpected": True})})
    with pytest.raises(WarehouseError):
        make_adapter(transport=transport).execute(make_plan(), timeout_seconds=10.0)


def test_non_json_body_maps_to_warehouse_error() -> None:
    transport = RecordingTransport({"*": httpx.Response(200, text="not json")})
    with pytest.raises(WarehouseError):
        make_adapter(transport=transport).execute(make_plan(), timeout_seconds=10.0)


# ---------------------------------------------------------------------------
# Unmappable governed members are refused before any HTTP call
# ---------------------------------------------------------------------------
def test_unmapped_dimension_refused_without_http_call() -> None:
    """Week Number has no member in cube/model/FactSales.js."""
    transport = RecordingTransport({"*": success_response()})
    with pytest.raises(WarehouseError) as excinfo:
        make_adapter(transport=transport).execute(
            make_plan(
                {
                    "measures": ["Revenue"],
                    "dimensions": ["Week Number"],
                    "filters": [],
                    "timeDimensions": [],
                }
            ),
            timeout_seconds=10.0,
        )
    assert "Week Number" in str(excinfo.value)
    assert "was not sent to Cube" in str(excinfo.value)
    assert transport.requests == []


def test_unmapped_metric_refused_without_http_call() -> None:
    transport = RecordingTransport({"*": success_response()})
    with pytest.raises(WarehouseError):
        make_adapter(transport=transport).execute(
            make_plan(
                {
                    "measures": ["Discount"],
                    "dimensions": [],
                    "filters": [],
                    "timeDimensions": [],
                }
            ),
            timeout_seconds=10.0,
        )
    assert transport.requests == []


def test_year_as_plain_dimension_refused_with_actionable_message() -> None:
    """Year is a time attribute: only expressible via timeDimensions granularity."""
    transport = RecordingTransport({"*": success_response()})
    with pytest.raises(WarehouseError) as excinfo:
        make_adapter(transport=transport).execute(
            make_plan(
                {
                    "measures": ["Revenue"],
                    "dimensions": ["Year"],
                    "filters": [],
                    "timeDimensions": [],
                }
            ),
            timeout_seconds=10.0,
        )
    message = str(excinfo.value)
    assert "Year" in message and "timeDimensions" in message
    assert transport.requests == []


def test_year_filter_refused_without_http_call() -> None:
    transport = RecordingTransport({"*": success_response()})
    with pytest.raises(WarehouseError) as excinfo:
        make_adapter(transport=transport).execute(
            make_plan(
                {
                    "measures": ["Revenue"],
                    "dimensions": [],
                    "filters": [{"member": "Year", "operator": "equals", "values": [2023]}],
                    "timeDimensions": [],
                }
            ),
            timeout_seconds=10.0,
        )
    assert "Year" in str(excinfo.value)
    assert transport.requests == []


def test_plan_without_cube_payload_is_refused() -> None:
    """A plan not produced by the governed compiler never reaches Cube."""
    transport = RecordingTransport({"*": success_response()})
    plan = QueryPlan(sql="SELECT 1", cube_payload=None)
    with pytest.raises(WarehouseError):
        make_adapter(transport=transport).execute(plan, timeout_seconds=10.0)
    assert transport.requests == []


# ---------------------------------------------------------------------------
# End to end: chat over Cube with zero route changes
# ---------------------------------------------------------------------------
def test_chat_endpoint_works_over_cube_without_route_changes() -> None:
    """Real routes, real translation, real compiler — only HTTP and the agent stubbed."""
    transport = RecordingTransport(
        {
            "*": httpx.Response(
                200,
                json={
                    "data": [
                        {"FactSales.country": "United States", "FactSales.revenue": "12642905.0"},
                        {"FactSales.country": "Australia", "FactSales.revenue": "925000.5"},
                    ]
                },
            )
        }
    )
    cube_adapter = make_adapter(transport=transport)
    stub_agent = StubAgentAdapter(
        {
            "Show sales by country": agent_output(
                "Show sales by country", metric="Sales", dimension="Country"
            )
        }
    )

    app = create_app()
    app.dependency_overrides[get_warehouse] = lambda: cube_adapter
    app.dependency_overrides[get_agent_service] = lambda: AgentService(adapter=stub_agent)
    client = TestClient(app)

    response = client.post("/api/v1/chat/query", json={"question": "Show sales by country"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "answered"
    assert body["data"] == [
        {"Country": "United States", "Revenue": 12642905.0},
        {"Country": "Australia", "Revenue": 925000.5},
    ]

    # The governed contract is intact end to end.
    assert body["evidence"]["governed_metric"] == "Revenue"
    assert body["evidence"]["governed_query"]["measures"] == ["Revenue"]
    assert body["evidence"]["source_model"] == "METRICMIND.MART.FACT_SALES"

    # Exactly one /load POST went to Cube, carrying governed content only.
    assert len(transport.requests) == 1
    body_sent = json.loads(transport.requests[0].content)
    assert body_sent == {
        "query": {
            "measures": ["FactSales.revenue"],
            "dimensions": ["FactSales.country"],
            "filters": [],
            "timeDimensions": [],
        }
    }


def test_chat_endpoint_surfaces_cube_failure_as_502() -> None:
    """A Cube outage is a structured 502, not a raw exception."""
    transport = RecordingTransport(exc=httpx.ConnectError("connection refused"))
    cube_adapter = make_adapter(transport=transport)
    stub_agent = StubAgentAdapter(
        {
            "Show sales by country": agent_output(
                "Show sales by country", metric="Sales", dimension="Country"
            )
        }
    )

    app = create_app()
    app.dependency_overrides[get_warehouse] = lambda: cube_adapter
    app.dependency_overrides[get_agent_service] = lambda: AgentService(adapter=stub_agent)
    client = TestClient(app)

    response = client.post("/api/v1/chat/query", json={"question": "Show sales by country"})

    assert response.status_code == 502
    error = response.json()["error"]
    assert error["code"] == "warehouse_error"
    assert "could not be reached" in error["message"]
    assert "connection refused" not in error["message"]


# ---------------------------------------------------------------------------
# Backward compatibility of QueryPlan
# ---------------------------------------------------------------------------
def test_query_plan_defaults_are_unchanged() -> None:
    """Existing constructions (tests, conftest, code) keep working unchanged."""
    plan = QueryPlan(sql="SELECT 1")
    assert plan.parameters == []
    assert plan.source_model == ""
    assert plan.columns == []
    assert plan.cube_payload is None
