"""Shared test fixtures.

No test in this suite requires Snowflake credentials or a running Ollama
server. The warehouse is replaced by FakeWarehouse and the AI agent is
replaced by StubAgentAdapter through FastAPI dependency overrides.

This keeps the tests deterministic while still exercising the real routes,
governed registry, translation, compilation, validation, and error handling.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

import pytest
from fastapi.testclient import TestClient

from app.adapters.warehouse import (
    QueryPlan,
    QueryResult,
    WarehouseAdapter,
    get_warehouse,
)
from app.core.errors import ConfigurationError, WarehouseError
from app.main import create_app
from app.services.agent_service import AgentService, get_agent_service


class FakeWarehouse(WarehouseAdapter):
    """In-memory warehouse stand-in.

    Records every plan it is asked to run so tests can assert on the compiled
    SQL and warehouse behavior.
    """

    name = "fake"

    def __init__(
        self,
        rows: Optional[List[Dict[str, Any]]] = None,
        columns: Optional[List[str]] = None,
        configured: bool = True,
        raises: Optional[Exception] = None,
    ) -> None:
        self._rows = rows if rows is not None else []
        self._columns = columns or []
        self._configured = configured
        self._raises = raises
        self.executed_plans: List[QueryPlan] = []

    def is_configured(self) -> bool:
        return self._configured

    def missing_settings(self) -> List[str]:
        if self._configured:
            return []

        return [
            "SNOWFLAKE_ACCOUNT",
            "SNOWFLAKE_USER",
            "SNOWFLAKE_PASSWORD",
            "SNOWFLAKE_WAREHOUSE",
        ]

    def execute(
        self,
        plan: QueryPlan,
        timeout_seconds: float,
    ) -> QueryResult:
        self.executed_plans.append(plan)

        if not self._configured:
            raise ConfigurationError(
                "The 'fake' warehouse backend is not configured. "
                "Missing environment settings: SNOWFLAKE_ACCOUNT."
            )

        if self._raises is not None:
            raise self._raises

        columns = self._columns or plan.columns

        rows = [
            {
                column: row.get(column)
                for column in (columns or row.keys())
            }
            for row in self._rows
        ]

        return QueryResult(
            rows=rows,
            columns=columns,
            source_model=plan.source_model,
        )


class StubAgentAdapter:
    """Deterministic replacement for the real Llama/Ollama agent.

    The real agent is intentionally not used in backend tests because GitHub
    CI does not run an Ollama server. This adapter returns the same dictionary
    shape as the real agent.
    """

    name = "stub-agent"

    def __init__(
        self,
        responses: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        self._responses = responses or {}
        self.questions: List[str] = []

    @property
    def available(self) -> bool:
        return True

    @property
    def availability_detail(self) -> Optional[str]:
        return None

    @property
    def declared_metrics(self) -> List[str]:
        return [
            "Sales",
            "Revenue",
            "Profit",
            "Profit Margin",
            "Orders",
            "Customers",
            "Quantity",
            "Quantity Sold",
            "Shipping Cost",
            "Average Order Value",
        ]

    @property
    def declared_dimensions(self) -> List[str]:
        return [
            "Year",
            "Country",
            "Market",
            "Region",
            "Category",
            "Sub-Category",
            "Product Name",
            "Ship Mode",
            "Order Priority",
        ]

    def interpret(self, question: str) -> Dict[str, Any]:
        """Return deterministic agent output for a test question."""

        self.questions.append(question)

        if question in self._responses:
            return dict(self._responses[question])

        # Keep unsupported/unknown questions deterministic.
        # This intentionally does not guess a metric or dimension.
        return {
            "question": question,
            "metric": None,
            "dimension": None,
            "filters": {"Year": None},
            "operation": None,
            "ambiguity": {
                "ambiguous": False,
                "reason": None,
                "possible_metrics": [],
            },
        }


def agent_output(
    question: str,
    metric: Optional[str] = None,
    dimension: Optional[str] = None,
    operation: Optional[str] = None,
    year: Optional[int] = None,
    ambiguous: bool = False,
    reason: Optional[str] = None,
    possible_metrics: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    """Build an agent-shaped output dictionary."""

    return {
        "question": question,
        "metric": metric,
        "dimension": dimension,
        "filters": {
            "Year": year,
        },
        "operation": operation,
        "ambiguity": {
            "ambiguous": ambiguous,
            "reason": reason,
            "possible_metrics": list(
                possible_metrics or []
            ),
        },
    }


@pytest.fixture
def fake_warehouse() -> FakeWarehouse:
    """Configured fake warehouse with deterministic result rows."""

    return FakeWarehouse(
        rows=[
            {
                "Country": "United States",
                "Revenue": 12642905.0,
            },
            {
                "Country": "Australia",
                "Revenue": 925000.5,
            },
        ]
    )


@pytest.fixture
def stub_agent() -> StubAgentAdapter:
    """Deterministic replacement for the Llama/Ollama agent."""

    return StubAgentAdapter(
        {
            "Show sales by country": agent_output(
                "Show sales by country",
                metric="Sales",
                dimension="Country",
            ),

            "Show total sales by country in 2023": agent_output(
                "Show total sales by country in 2023",
                metric="Sales",
                dimension="Country",
                year=2023,
            ),

            "Which is the best category?": agent_output(
                "Which is the best category?",
                ambiguous=True,
                reason=(
                    "'best' does not specify which metric "
                    "should be used."
                ),
                possible_metrics=[
                    "Sales",
                    "Profit",
                    "Quantity",
                ],
            ),

            "Show total discount by country": agent_output(
                "Show total discount by country",
                metric="Discount",
                dimension="Country",
            ),
        }
    )


@pytest.fixture
def client(
    fake_warehouse: FakeWarehouse,
    stub_agent: StubAgentAdapter,
) -> TestClient:
    """Test client with deterministic agent and warehouse replacements."""

    app = create_app()

    app.dependency_overrides[get_warehouse] = (
        lambda: fake_warehouse
    )

    app.dependency_overrides[get_agent_service] = (
        lambda: AgentService(adapter=stub_agent)
    )

    return TestClient(app)


@pytest.fixture
def stub_client(
    stub_agent: StubAgentAdapter,
    fake_warehouse: FakeWarehouse,
) -> TestClient:
    """Test client with both agent and warehouse replaced."""

    app = create_app()

    app.dependency_overrides[get_warehouse] = (
        lambda: fake_warehouse
    )

    app.dependency_overrides[get_agent_service] = (
        lambda: AgentService(adapter=stub_agent)
    )

    return TestClient(app)


@pytest.fixture
def unavailable_client(
    stub_agent: StubAgentAdapter,
) -> TestClient:
    """Test client whose warehouse reports itself unconfigured.

    The agent is still stubbed so the test never depends on Ollama.
    """

    app = create_app()

    app.dependency_overrides[get_warehouse] = (
        lambda: FakeWarehouse(configured=False)
    )

    app.dependency_overrides[get_agent_service] = (
        lambda: AgentService(adapter=stub_agent)
    )

    return TestClient(app)


@pytest.fixture
def failing_client(
    stub_agent: StubAgentAdapter,
) -> TestClient:
    """Test client whose warehouse raises a generic failure.

    The agent is still stubbed so the test never depends on Ollama.
    """

    app = create_app()

    app.dependency_overrides[get_warehouse] = (
        lambda: FakeWarehouse(
            raises=WarehouseError(
                "The warehouse query failed."
            )
        )
    )

    app.dependency_overrides[get_agent_service] = (
        lambda: AgentService(adapter=stub_agent)
    )

    return TestClient(app)