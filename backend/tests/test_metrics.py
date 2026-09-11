"""Metrics and dimensions catalogue tests (requirements 2 and 3).

The formula assertions are the important ones: they pin the governed registry to
docs/metric_dictionary.md, so an accidental edit to a formula fails the suite.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

# Exactly the formulas in docs/metric_dictionary.md (section 2 summary table and
# section 14 "Metric Governance Rules").
EXPECTED_FORMULAS = {
    "Revenue": "SUM(SALES)",
    "Profit": "SUM(PROFIT)",
    "Profit Margin": "SUM(PROFIT) / SUM(SALES) x 100",
    "Orders": "COUNT(DISTINCT ORDER_ID)",
    "Customers": "COUNT(DISTINCT CUSTOMER_ID)",
    "Quantity Sold": "SUM(QUANTITY)",
    "Shipping Cost": "SUM(SHIPPING_COST)",
    "Average Order Value": "SUM(SALES) / COUNT(DISTINCT ORDER_ID)",
}


def test_metrics_endpoint_returns_eight_governed_metrics(client: TestClient) -> None:
    response = client.get("/api/v1/metrics")

    assert response.status_code == 200
    body = response.json()

    assert body["count"] == 8
    assert body["source_document"] == "docs/metric_dictionary.md"
    assert {metric["name"] for metric in body["metrics"]} == set(EXPECTED_FORMULAS)


def test_metric_formulas_match_the_metric_dictionary(client: TestClient) -> None:
    metrics = {metric["name"]: metric for metric in client.get("/api/v1/metrics").json()["metrics"]}

    for name, formula in EXPECTED_FORMULAS.items():
        assert metrics[name]["formula"] == formula, f"{name} formula drifted from the dictionary"


def test_ratio_metrics_are_marked_non_additive(client: TestClient) -> None:
    """Profit Margin must never be summed; the flag makes that machine-checkable."""
    metrics = {metric["name"]: metric for metric in client.get("/api/v1/metrics").json()["metrics"]}

    assert metrics["Profit Margin"]["additive"] is False
    assert metrics["Average Order Value"]["additive"] is False
    assert metrics["Orders"]["additive"] is False
    assert metrics["Revenue"]["additive"] is True
    assert "NULLIF" in metrics["Profit Margin"]["sql_expression"]


def test_metrics_endpoint_reports_the_governance_conflict(client: TestClient) -> None:
    """The agent/dictionary metric mismatch is surfaced, not hidden."""
    notes = " ".join(client.get("/api/v1/metrics").json()["notes"])

    assert "Discount" in notes
    assert "Sales" in notes and "Revenue" in notes


def test_agent_sales_alias_is_declared_on_revenue(client: TestClient) -> None:
    metrics = {metric["name"]: metric for metric in client.get("/api/v1/metrics").json()["metrics"]}

    assert "Sales" in metrics["Revenue"]["aliases"]
    assert "Quantity" in metrics["Quantity Sold"]["aliases"]


def test_dimensions_endpoint_lists_governed_and_ungoverned(client: TestClient) -> None:
    response = client.get("/api/v1/dimensions")

    assert response.status_code == 200
    body = response.json()

    assert body["count"] == 17
    assert body["governed_count"] == 12

    by_name = {dimension["name"]: dimension for dimension in body["dimensions"]}

    # Governed by docs/metric_dictionary.md sections 12 and 13.
    for name in ("Country", "Region", "Market", "City", "State", "Year", "Quarter"):
        assert by_name[name]["governed"] is True, f"{name} should be governed"

    # Physical dbt columns that the metric dictionary does not list.
    for name in ("Category", "Sub-Category", "Product Name", "Ship Mode", "Order Priority"):
        assert by_name[name]["governed"] is False, f"{name} should be flagged ungoverned"


def test_dimensions_expose_source_model_and_column(client: TestClient) -> None:
    """The frontend/Evidence panel needs to know where each dimension comes from."""
    by_name = {
        dimension["name"]: dimension
        for dimension in client.get("/api/v1/dimensions").json()["dimensions"]
    }

    assert by_name["Country"]["source_model"] == "fact_sales"
    assert by_name["Country"]["column"] == "COUNTRY"
    assert by_name["Category"]["source_model"] == "dim_product"
    assert by_name["Category"]["join_key"] == "PRODUCT_ID"
    assert by_name["Quarter"]["source_model"] == "dim_date"


def test_europe_governance_note_is_exposed(client: TestClient) -> None:
    """MARKET = 'EU' rather than REGION = 'Europe' is a documented trap."""
    notes = " ".join(client.get("/api/v1/dimensions").json()["notes"])

    assert "MARKET = 'EU'" in notes
