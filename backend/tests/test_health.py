"""Health endpoint tests (requirement 1).

These also assert the health payload leaks nothing sensitive.
"""

from __future__ import annotations

import json

from fastapi.testclient import TestClient


def test_health_endpoint_returns_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["service"]
    assert body["version"]
    assert body["agent_available"] is True
    assert body["governed_metric_count"] == 8
    assert body["governed_dimension_count"] == 17
    assert body["warehouse"]["backend"] == "fake"
    assert body["warehouse"]["configured"] is True


def test_health_reports_the_agents_own_metric_vocabulary(client: TestClient) -> None:
    """The agent's declared metrics are reported, not silently rewritten."""
    body = client.get("/api/v1/health").json()

    assert body["agent_declared_metrics"] == [
        "Sales",
        "Profit",
        "Quantity",
        "Discount",
        "Shipping Cost",
    ]
    assert "Category" in body["agent_declared_dimensions"]


def test_top_level_health_alias_exists(client: TestClient) -> None:
    """``/health`` is available for local development probes."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_is_degraded_without_warehouse_credentials(
    unavailable_client: TestClient,
) -> None:
    """Missing credentials degrade health; they do not break the application."""
    response = unavailable_client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "degraded"
    assert body["warehouse"]["configured"] is False
    # Missing setting *names* are reported so the operator knows what to set.
    assert "SNOWFLAKE_ACCOUNT" in body["warehouse"]["missing_settings"]
    assert body["agent_available"] is True


def test_health_does_not_leak_credentials(client: TestClient) -> None:
    """No secret-shaped value or key appears anywhere in the payload."""
    raw = json.dumps(client.get("/api/v1/health").json()).lower()

    for forbidden in ("password", "snowflake_account", "account=", "user=", "token", "secret"):
        assert forbidden not in raw

    warehouse_keys = set(client.get("/api/v1/health").json()["warehouse"].keys())
    assert warehouse_keys == {
        "backend",
        "database",
        "schema",
        "configured",
        "missing_settings",
    }
