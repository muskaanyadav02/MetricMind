"""Chat endpoint tests (requirements 4, 5, 6, 9, 10).

Some tests drive the *real* local AI agent (``ai agent/query_builder.py``) to
prove the integration works end to end; others use the stub agent so the
warehouse-side behaviour can be asserted deterministically.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import FakeWarehouse

CHAT_URL = "/api/v1/chat/query"


# ---------------------------------------------------------------------------
# Requirement 4: a valid chat request, with mocked agent and warehouse
# ---------------------------------------------------------------------------
def test_chat_answered_with_stubbed_agent_and_warehouse(stub_client: TestClient) -> None:
    response = stub_client.post(CHAT_URL, json={"question": "Show sales by country"})

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "answered"
    assert body["message"] is None
    assert body["answer"]
    assert body["data"][0]["Country"] == "United States"

    evidence = body["evidence"]
    assert evidence["question"] == "Show sales by country"
    assert evidence["interpreted_metric"] == "Sales"
    assert evidence["governed_metric"] == "Revenue"
    assert evidence["metric_formula"] == "SUM(SALES)"
    assert evidence["dimensions"] == ["Country"]
    assert evidence["governed_query"]["measures"] == ["Revenue"]
    assert evidence["governed_query"]["dimensions"] == ["Country"]
    assert evidence["row_count"] == 2
    assert evidence["source_model"] == "METRICMIND.MART.FACT_SALES"
    assert evidence["answer_generation"] == "deterministic"
    assert evidence["validation"] is not None


def test_chat_evidence_preserves_the_agents_raw_output(stub_client: TestClient) -> None:
    """The agent's dictionary is returned unmodified for audit."""
    body = stub_client.post(CHAT_URL, json={"question": "Show sales by country"}).json()

    agent_output = body["evidence"]["agent_output"]
    assert agent_output["metric"] == "Sales"
    assert agent_output["dimension"] == "Country"
    assert set(agent_output) == {"question", "metric", "dimension", "filters", "operation", "ambiguity"}


def test_chat_reports_every_translation_it_made(stub_client: TestClient) -> None:
    """Sales -> Revenue is an explicit, reported interpretation."""
    notes = " ".join(stub_client.post(CHAT_URL, json={"question": "Show sales by country"}).json()["evidence"]["translation_notes"])

    assert "Sales" in notes and "Revenue" in notes


# ---------------------------------------------------------------------------
# Real agent integration
# ---------------------------------------------------------------------------
def test_chat_with_the_real_agent(client: TestClient) -> None:
    """Drives the actual 'ai agent/' module, loaded despite the space in its name."""
    response = client.post(CHAT_URL, json={"question": "Show sales by country"})

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "answered"
    assert body["evidence"]["interpreted_metric"] == "Sales"
    assert body["evidence"]["governed_metric"] == "Revenue"
    assert body["evidence"]["dimensions"] == ["Country"]


def test_real_agent_year_filter_becomes_a_governed_filter(client: TestClient) -> None:
    response = client.post(CHAT_URL, json={"question": "Show total sales by country in 2023"})

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "answered"
    filters = body["evidence"]["governed_query"]["filters"]
    assert filters == [{"member": "Year", "operator": "equals", "values": [2023]}]


# ---------------------------------------------------------------------------
# Requirement 5: ambiguous and unsupported questions
# ---------------------------------------------------------------------------
def test_ambiguous_question_returns_ambiguous_status(stub_client: TestClient) -> None:
    response = stub_client.post(CHAT_URL, json={"question": "Which is the best category?"})

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ambiguous"
    assert body["answer"] is None
    assert body["message"]
    assert body["ambiguity"]["ambiguous"] is True
    assert body["ambiguity"]["possible_metrics"] == ["Sales", "Profit", "Quantity"]
    assert body["data"] == []
    assert body["evidence"]["governed_query"] is None
    assert body["evidence"]["validation"]["status"] == "SKIPPED"


def test_real_agent_ambiguous_question_is_not_executed(
    client: TestClient, fake_warehouse: FakeWarehouse
) -> None:
    """The real agent flags 'best' as ambiguous; no query must reach the warehouse."""
    response = client.post(CHAT_URL, json={"question": "Which is the best category?"})

    assert response.status_code == 200
    assert response.json()["status"] == "ambiguous"
    assert fake_warehouse.executed_plans == []


def test_ungoverned_metric_is_refused(client: TestClient, fake_warehouse: FakeWarehouse) -> None:
    """The agent offers 'Discount'; the governed dictionary does not define it."""
    response = client.post(CHAT_URL, json={"question": "Show total discount by country"})

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "unsupported"
    assert "Discount" in body["message"]
    assert body["answer"] is None
    assert fake_warehouse.executed_plans == []


def test_question_without_a_metric_is_unsupported(
    client: TestClient, fake_warehouse: FakeWarehouse
) -> None:
    response = client.post(CHAT_URL, json={"question": "Show customer happiness by country"})

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "unsupported"
    assert body["message"]
    assert fake_warehouse.executed_plans == []


def test_average_operation_is_refused_rather_than_guessed(client: TestClient) -> None:
    """'average' has no governed meaning; refusing beats inventing an AVG()."""
    response = client.post(CHAT_URL, json={"question": "What is the average sales by market?"})

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "unsupported"
    assert "average" in body["message"].lower()


def test_unsupported_question_still_reports_schema_validation_as_skipped(
    client: TestClient,
) -> None:
    body = client.post(CHAT_URL, json={"question": "Show customer happiness by country"}).json()

    assert body["evidence"]["validation"]["status"] == "SKIPPED"
    assert body["evidence"]["validation"]["is_valid"] is False


# ---------------------------------------------------------------------------
# Requirement 6: invalid request payloads
# ---------------------------------------------------------------------------
def test_question_that_is_too_short_is_rejected(client: TestClient) -> None:
    response = client.post(CHAT_URL, json={"question": "hi"})

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "request_validation_error"
    assert any(detail["field"] == "question" for detail in body["error"]["details"])


def test_missing_question_is_rejected(client: TestClient) -> None:
    response = client.post(CHAT_URL, json={})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "request_validation_error"


def test_non_string_question_is_rejected(client: TestClient) -> None:
    response = client.post(CHAT_URL, json={"question": 12345})

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Requirement 10: raw SQL cannot be submitted through the API
# ---------------------------------------------------------------------------
def test_raw_sql_field_is_rejected(client: TestClient) -> None:
    response = client.post(
        CHAT_URL,
        json={"question": "Show sales by country", "sql": "SELECT * FROM METRICMIND.MART.fact_sales"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "request_validation_error"
    assert any(detail["field"] == "sql" for detail in body["error"]["details"])


def test_unknown_fields_are_rejected_outright(client: TestClient) -> None:
    """``extra="forbid"`` means there is no smuggling channel at all."""
    for payload in (
        {"question": "Show sales by country", "query": "DROP TABLE fact_sales"},
        {"question": "Show sales by country", "measures_raw": ["SUM(SALES)"]},
        {"question": "Show sales by country", "filters_raw": "1=1"},
    ):
        response = client.post(CHAT_URL, json=payload)
        assert response.status_code == 422, payload


def test_client_cannot_choose_the_sql_identifiers(client: TestClient) -> None:
    """Even a syntactically valid governed query cannot name arbitrary columns."""
    response = client.post(
        CHAT_URL,
        json={"question": "Show sales by country", "governed_query": {"measures": ["1; DROP TABLE x"]}},
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Requirement 9: warehouse unavailable / configuration error
# ---------------------------------------------------------------------------
def test_warehouse_not_configured_returns_503(unavailable_client: TestClient) -> None:
    response = unavailable_client.post(CHAT_URL, json={"question": "Show sales by country"})

    assert response.status_code == 503
    body = response.json()

    assert body["error"]["code"] == "configuration_error"
    assert "SNOWFLAKE_ACCOUNT" in body["error"]["message"]
    # No fake data is returned in place of a real result.
    assert "data" not in body


def test_warehouse_error_returns_502_without_leaking_details(
    failing_client: TestClient,
) -> None:
    response = failing_client.post(CHAT_URL, json={"question": "Show sales by country"})

    assert response.status_code == 502
    body = response.json()

    assert body["error"]["code"] == "warehouse_error"
    assert body["error"]["message"] == "The warehouse query failed."


def test_error_responses_carry_a_correlation_id(failing_client: TestClient) -> None:
    body = failing_client.post(CHAT_URL, json={"question": "Show sales by country"}).json()

    assert body["error"]["correlation_id"]
