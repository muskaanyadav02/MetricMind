"""Shared test fixtures.

No test in this suite requires Snowflake credentials. The warehouse is replaced
by :class:`FakeWarehouse` through FastAPI's dependency overrides, and the
warehouse *interface* is what gets substituted - so the tests exercise the real
routes, the real governed registry, the real translation and compilation logic,
and the real validators.
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

    Records every plan it is asked to run so tests can assert on the compiled SQL.
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
        return ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD", "SNOWFLAKE_WAREHOUSE"]

    def execute(self, plan: QueryPlan, timeout_seconds: float) -> QueryResult:
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
            {column: row.get(column) for column in (columns or row.keys())}
            for row in self._rows
        ]
        return QueryResult(rows=rows, columns=columns, source_model=plan.source_model)


class StubAgentAdapter:
    """Stands in for :class:`~app.adapters.agent_loader.LocalAgentAdapter`.

    Returns canned output per question, matching the real agent's dictionary
    shape exactly (question / metric / dimension / filters / operation /
    ambiguity).
    """

    name = "stub-agent"

    def __init__(self, responses: Dict[str, Dict[str, Any]]) -> None:
        self._responses = responses
        self.questions: List[str] = []

    @property
    def available(self) -> bool:
        return True

    @property
    def availability_detail(self) -> Optional[str]:
        return None

    @property
    def declared_metrics(self) -> List[str]:
        return ["Sales", "Profit", "Quantity", "Discount", "Shipping Cost"]

    @property
    def declared_dimensions(self) -> List[str]:
        return ["Year", "Country", "Market", "Region", "Category"]

    def interpret(self, question: str) -> Dict[str, Any]:
        self.questions.append(question)
        if question in self._responses:
            return dict(self._responses[question])
        return {
            "question": question,
            "metric": None,
            "dimension": None,
            "filters": {"Year": None},
            "operation": None,
            "ambiguity": {"ambiguous": False, "reason": None, "possible_metrics": []},
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
        "filters": {"Year": year},
        "operation": operation,
        "ambiguity": {
            "ambiguous": ambiguous,
            "reason": reason,
            "possible_metrics": list(possible_metrics or []),
        },
    }


@pytest.fixture
def fake_warehouse() -> FakeWarehouse:
    return FakeWarehouse(
        rows=[
            {"Country": "United States", "Revenue": 12642905.0},
            {"Country": "Australia", "Revenue": 925000.5},
        ]
    )


@pytest.fixture
def client(fake_warehouse: FakeWarehouse) -> TestClient:
    """Test client with the warehouse replaced by the fake."""
    app = create_app()
    app.dependency_overrides[get_warehouse] = lambda: fake_warehouse
    return TestClient(app)


@pytest.fixture
def stub_agent() -> StubAgentAdapter:
    return StubAgentAdapter(
        {
            "Show sales by country": agent_output(
                "Show sales by country", metric="Sales", dimension="Country"
            ),
            "Which is the best category?": agent_output(
                "Which is the best category?",
                ambiguous=True,
                reason="'best' does not specify which metric should be used.",
                possible_metrics=["Sales", "Profit", "Quantity"],
            ),
            "Show total discount by country": agent_output(
                "Show total discount by country", metric="Discount", dimension="Country"
            ),
        }
    )


@pytest.fixture
def stub_client(stub_agent: StubAgentAdapter, fake_warehouse: FakeWarehouse) -> TestClient:
    """Test client with both the agent and the warehouse replaced."""
    app = create_app()
    app.dependency_overrides[get_warehouse] = lambda: fake_warehouse
    app.dependency_overrides[get_agent_service] = lambda: AgentService(adapter=stub_agent)
    return TestClient(app)


@pytest.fixture
def unavailable_client() -> TestClient:
    """Test client whose warehouse reports itself unconfigured."""
    app = create_app()
    app.dependency_overrides[get_warehouse] = lambda: FakeWarehouse(configured=False)
    return TestClient(app)


@pytest.fixture
def failing_client() -> TestClient:
    """Test client whose warehouse raises a generic failure."""
    app = create_app()
    app.dependency_overrides[get_warehouse] = lambda: FakeWarehouse(
        raises=WarehouseError("The warehouse query failed.")
    )
    return TestClient(app)
