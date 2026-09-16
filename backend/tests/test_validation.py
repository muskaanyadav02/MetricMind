"""Translation, compilation and validation-normalisation tests.

Three groups:

* **Requirement 7** - the AI agent's output becomes a governed semantic query.
  These call :func:`~app.services.query_service.translate_agent_output` directly
  so every branch (rename, refusal, ambiguity) is asserted explicitly.
* **Compilation** - governed queries become parameterised SQL. The important
  assertions are that identifiers come only from the registry and that filter
  values are bind parameters, never SQL text.
* **Requirement 8** - the validators' three mutually incompatible return shapes
  are normalised into one report, and an unrecognised shape fails closed.

The normalisation tests import the private helpers on purpose: they are the
normalisation contract, and asserting them directly is the only way to prove a
tuple and a dict produce the same report without needing the warehouse.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.adapters.warehouse import validate_identifier
from app.config import get_settings
from app.core.errors import ConfigurationError, ValidationFailedError
from app.schemas.chat import AmbiguityInfo
from app.schemas.semantic import GovernedQuery, OrderBy, QueryFilter
from app.services.agent_service import AgentInterpretation
from app.services.metric_service import FACT_SALES, GovernedRegistry, get_metric_service
from app.services.query_service import (
    build_cube_payload,
    compile_governed_query,
    translate_agent_output,
)
from app.services.validation_service import (
    _normalize_data_result,
    _normalize_schema_result,
    get_validation_service,
)

REGISTRY = get_metric_service()
SETTINGS = get_settings()


def interpretation(
    question: str = "Show sales by country",
    *,
    metric: str | None = None,
    dimension: str | None = None,
    operation: str | None = None,
    year: int | None = None,
    ambiguous: bool = False,
    reason: str | None = None,
    possible_metrics: tuple[str, ...] = (),
) -> AgentInterpretation:
    """Build an :class:`AgentInterpretation` shaped exactly like the agent's."""
    return AgentInterpretation(
        question=question,
        raw={
            "question": question,
            "metric": metric,
            "dimension": dimension,
            "filters": {"Year": year},
            "operation": operation,
            "ambiguity": {
                "ambiguous": ambiguous,
                "reason": reason,
                "possible_metrics": list(possible_metrics),
            },
        },
        metric=metric,
        dimension=dimension,
        operation=operation,
        year=year,
        ambiguity=AmbiguityInfo(
            ambiguous=ambiguous, reason=reason, possible_metrics=list(possible_metrics)
        ),
    )


def translate(agent_interpretation: AgentInterpretation):
    return translate_agent_output(
        agent_interpretation,
        REGISTRY,
        default_limit=SETTINGS.default_result_rows,
        max_limit=SETTINGS.max_result_rows,
    )


# ===========================================================================
# Requirement 7: agent output -> governed semantic query
# ===========================================================================
def test_agent_sales_becomes_the_governed_metric_revenue() -> None:
    outcome = translate(interpretation("Show sales by country", metric="Sales", dimension="Country"))

    assert outcome.status == "ok"
    assert outcome.governed_query is not None
    assert outcome.governed_query.measures == ["Revenue"]
    assert outcome.governed_query.dimensions == ["Country"]


def test_agent_quantity_becomes_the_governed_metric_quantity_sold() -> None:
    outcome = translate(interpretation("Show quantity by market", metric="Quantity", dimension="Market"))

    assert outcome.status == "ok"
    assert outcome.governed_query is not None
    assert outcome.governed_query.measures == ["Quantity Sold"]


def test_a_metric_that_needs_no_rename_is_not_reported_as_renamed() -> None:
    outcome = translate(interpretation("Show profit by country", metric="Profit", dimension="Country"))

    assert outcome.status == "ok"
    assert not any("was interpreted as the governed metric" in note for note in outcome.notes)


def test_every_translation_decision_is_reported_in_the_notes() -> None:
    """Nothing is inferred silently: the rename and the ordering both appear."""
    outcome = translate(interpretation("Show sales by country", metric="Sales", dimension="Country"))
    notes = " ".join(outcome.notes)

    assert "Sales" in notes and "Revenue" in notes
    assert "Revenue DESC" in notes


def test_agent_year_filter_becomes_a_filter_on_the_governed_year_dimension() -> None:
    outcome = translate(
        interpretation("Show sales by country in 2023", metric="Sales", dimension="Country", year=2023)
    )

    assert outcome.status == "ok"
    assert outcome.governed_query is not None
    assert outcome.governed_query.filters == [
        QueryFilter(member="Year", operator="equals", values=[2023])
    ]


def test_highest_operation_becomes_a_descending_order_by() -> None:
    outcome = translate(
        interpretation("Which country has the highest sales?", metric="Sales", dimension="Country", operation="highest")
    )

    assert outcome.status == "ok"
    assert outcome.governed_query is not None
    assert outcome.governed_query.order_by == [OrderBy(member="Revenue", direction="desc")]


def test_lowest_operation_becomes_an_ascending_order_by() -> None:
    outcome = translate(
        interpretation("Which country has the lowest sales?", metric="Sales", dimension="Country", operation="lowest")
    )

    assert outcome.status == "ok"
    assert outcome.governed_query is not None
    assert outcome.governed_query.order_by == [OrderBy(member="Revenue", direction="asc")]


def test_ambiguous_agent_output_produces_an_ambiguous_outcome_without_a_query() -> None:
    outcome = translate(
        interpretation(
            "Which is the best category?",
            dimension="Category",
            ambiguous=True,
            reason="'best' does not specify which metric should be used.",
            possible_metrics=("Sales", "Profit", "Quantity"),
        )
    )

    assert outcome.status == "ambiguous"
    assert outcome.governed_query is None
    assert outcome.message
    assert outcome.ambiguity.possible_metrics == ["Sales", "Profit", "Quantity"]


def test_metric_absent_from_the_question_is_unsupported() -> None:
    outcome = translate(interpretation("Show customer happiness by country", dimension="Country"))

    assert outcome.status == "unsupported"
    assert outcome.governed_query is None
    assert "governed metric" in (outcome.message or "").lower()


def test_agent_discount_metric_is_refused_though_the_column_exists() -> None:
    """Discount is a real fact column but has no governed definition."""
    outcome = translate(interpretation("Show total discount by country", metric="Discount", dimension="Country"))

    assert outcome.status == "unsupported"
    assert outcome.governed_query is None
    assert "Discount" in (outcome.message or "")


def test_ungoverned_dimension_is_refused() -> None:
    outcome = translate(interpretation("Show sales by salesperson", metric="Sales", dimension="Salesperson"))

    assert outcome.status == "unsupported"
    assert outcome.governed_query is None
    assert "Salesperson" in (outcome.message or "")


def test_average_operation_is_refused_rather_than_invented() -> None:
    outcome = translate(
        interpretation("What is the average sales by market?", metric="Sales", dimension="Market", operation="average")
    )

    assert outcome.status == "unsupported"
    assert outcome.governed_query is None
    assert "Average Order Value" in (outcome.message or "")


def test_ungoverned_dimension_is_used_but_flagged_in_the_notes() -> None:
    """Category is a real mart column; it is allowed, and its status is reported."""
    outcome = translate(interpretation("Show sales by category", metric="Sales", dimension="Category"))

    assert outcome.status == "ok"
    assert outcome.governed_query is not None
    assert outcome.governed_query.dimensions == ["Category"]
    assert any("not listed in the governed metric dictionary" in note for note in outcome.notes)


# ===========================================================================
# Compilation: identifiers from the registry only, values always bound
# ===========================================================================
def test_compiled_sql_uses_governed_expressions_and_a_qualified_mart_table() -> None:
    plan = compile_governed_query(
        GovernedQuery(measures=["Revenue"], dimensions=["Country"]), REGISTRY, SETTINGS
    )

    assert "SUM(f.SALES) AS \"Revenue\"" in plan.sql
    assert "f.COUNTRY AS \"Country\"" in plan.sql
    assert f"FROM {plan.source_model}" in plan.sql
    # The dbt model is 'fact_sales'; Snowflake folds the unquoted name to uppercase.
    assert plan.source_model == f"METRICMIND.MART.{FACT_SALES.upper()}"
    assert plan.columns == ["Country", "Revenue"]


def test_filter_values_are_bound_parameters_and_never_sql_text() -> None:
    hostile = "United States' OR 1=1 --"
    plan = compile_governed_query(
        GovernedQuery(
            measures=["Revenue"],
            dimensions=["Country"],
            filters=[QueryFilter(member="Country", operator="equals", values=[hostile])],
        ),
        REGISTRY,
        SETTINGS,
    )

    assert hostile not in plan.sql
    assert plan.parameters == [hostile]
    assert "f.COUNTRY = %s" in plan.sql


def test_in_filters_bind_one_parameter_per_value() -> None:
    plan = compile_governed_query(
        GovernedQuery(
            measures=["Revenue"],
            dimensions=["Market"],
            filters=[QueryFilter(member="Market", operator="in", values=["EU", "US"])],
        ),
        REGISTRY,
        SETTINGS,
    )

    assert "f.MARKET IN (%s, %s)" in plan.sql
    assert plan.parameters == ["EU", "US"]


def test_contains_filter_binds_a_wildcard_parameter_rather_than_inlining_it() -> None:
    plan = compile_governed_query(
        GovernedQuery(
            measures=["Revenue"],
            filters=[QueryFilter(member="City", operator="contains", values=["New York"])],
        ),
        REGISTRY,
        SETTINGS,
    )

    assert "f.CITY ILIKE %s" in plan.sql
    assert plan.parameters == ["%New York%"]
    assert "New York" not in plan.sql


def test_a_dimension_from_another_mart_adds_a_join() -> None:
    plan = compile_governed_query(
        GovernedQuery(measures=["Revenue"], dimensions=["Category"]), REGISTRY, SETTINGS
    )

    assert "LEFT JOIN" in plan.sql
    assert "p.CATEGORY" in plan.sql
    assert "f.PRODUCT_ID = p.PRODUCT_ID" in plan.sql


def test_the_dim_date_join_casts_the_fact_timestamp() -> None:
    plan = compile_governed_query(
        GovernedQuery(measures=["Revenue"], dimensions=["Quarter"]), REGISTRY, SETTINGS
    )

    assert "CAST(f.ORDER_DATE AS DATE) = d.DATE_KEY" in plan.sql


def test_unknown_measure_is_rejected_before_any_sql_is_built() -> None:
    with pytest.raises(ValidationFailedError):
        compile_governed_query(
            GovernedQuery(measures=["DROP TABLE fact_sales"]), REGISTRY, SETTINGS
        )


def test_unknown_dimension_is_rejected() -> None:
    with pytest.raises(ValidationFailedError):
        compile_governed_query(
            GovernedQuery(measures=["Revenue"], dimensions=["1=1"]), REGISTRY, SETTINGS
        )


def test_unknown_filter_member_is_rejected() -> None:
    with pytest.raises(ValidationFailedError):
        compile_governed_query(
            GovernedQuery(
                measures=["Revenue"],
                filters=[QueryFilter(member="secret_column", values=["x"])],
            ),
            REGISTRY,
            SETTINGS,
        )


def test_order_by_an_unknown_member_is_rejected() -> None:
    with pytest.raises(ValidationFailedError):
        compile_governed_query(
            GovernedQuery(measures=["Revenue"], order_by=[OrderBy(member="; DROP TABLE x")]),
            REGISTRY,
            SETTINGS,
        )


def test_limit_is_clamped_to_the_configured_maximum() -> None:
    plan = compile_governed_query(
        GovernedQuery(measures=["Revenue"], limit=10_000), REGISTRY, SETTINGS
    )

    assert f"LIMIT {SETTINGS.max_result_rows}" in plan.sql
    assert "LIMIT 10000" not in plan.sql


def test_identifier_validation_rejects_anything_but_a_plain_column_name() -> None:
    """Defence in depth: even a registry-sourced identifier is re-checked."""
    for candidate in ("SALES", "SHIPPING_COST", "MARKET2"):
        assert validate_identifier(candidate) == candidate

    for candidate in ("sales", "SALES; DROP TABLE x", "SALES--", "f.SALES", "1=1", ""):
        with pytest.raises(ConfigurationError):
            validate_identifier(candidate)


def test_cube_payload_shape_matches_what_the_validator_expects() -> None:
    """The translation output is already in the Cube.dev payload shape."""
    payload = build_cube_payload(
        GovernedQuery(
            measures=["Revenue"],
            dimensions=["Market"],
            filters=[QueryFilter(member="Market", operator="in", values=["EU"])],
        )
    )

    assert set(payload) == {"measures", "dimensions", "filters", "timeDimensions"}
    assert payload["measures"] == ["Revenue"]
    assert payload["filters"] == [{"member": "Market", "operator": "in", "values": ["EU"]}]


def test_registry_lookup_tolerates_naming_variants() -> None:
    """The agent's 'Sub-Category' spelling meets the registry's 'Sub-Category'."""
    for variant in ("Sub-Category", "sub category", "SubCategory"):
        found = REGISTRY.find_dimension(variant)
        assert found is not None and found.name == "Sub-Category"


def test_registry_is_replaceable_without_touching_the_routes() -> None:
    """A Cube-backed registry can substitute this one; the interface is plain data."""
    empty = GovernedRegistry(metrics=[], dimensions=[])
    assert empty.metrics == []
    assert empty.find_metric("Revenue") is None


# ===========================================================================
# Requirement 8: validation result normalisation
# ===========================================================================
def test_schema_tuple_success_is_normalised() -> None:
    result = _normalize_schema_result((True, "Valid Payload"))

    assert result.is_valid is True
    assert result.message == "Valid Payload"


def test_schema_tuple_failure_keeps_the_validators_message() -> None:
    result = _normalize_schema_result((False, "'measures' is a required property"))

    assert result.is_valid is False
    assert "'measures' is a required property" in result.message


def test_schema_dict_shape_is_tolerated_for_forward_compatibility() -> None:
    result = _normalize_schema_result({"is_valid": False, "message": "bad"})

    assert result.is_valid is False
    assert result.message == "bad"


def test_unrecognised_schema_result_fails_closed() -> None:
    """A changed validator contract must never be read as 'valid'."""
    result = _normalize_schema_result(object())

    assert result.is_valid is False
    assert "Unrecognised" in result.message


def test_data_result_pass_shape_is_normalised() -> None:
    result, is_empty_failure = _normalize_data_result(
        {
            "status": "PASS",
            "row_count": 2,
            "null_count": 0,
            "invalid_discount_detected": False,
            "negative_sales_detected": False,
        }
    )

    assert is_empty_failure is False
    assert result.status == "PASS"
    assert result.row_count == 2
    assert result.raw["row_count"] == 2


def test_data_result_flagged_shape_is_normalised() -> None:
    result, _ = _normalize_data_result(
        {
            "status": "FLAGGED",
            "row_count": 3,
            "null_count": 1,
            "invalid_discount_detected": True,
            "negative_sales_detected": False,
        }
    )

    assert result.status == "FLAGGED"
    assert result.null_count == 1
    assert result.invalid_discount_detected is True
    assert result.negative_sales_detected is False


def test_data_result_empty_dataset_shape_is_normalised_as_a_failure() -> None:
    result, is_empty_failure = _normalize_data_result(
        {"status": "FAIL", "reason": "Empty dataset returned from Cube API."}
    )

    assert is_empty_failure is True
    assert result.status == "FAIL"
    assert result.reason == "Empty dataset returned from Cube API."
    assert result.row_count == 0


def test_unrecognised_data_result_fails_closed() -> None:
    result, is_empty_failure = _normalize_data_result("not a dict")

    assert is_empty_failure is True
    assert result.status == "FAIL"
    assert "Unrecognised" in (result.reason or "")


def test_data_validation_reports_the_heuristics_it_could_not_apply() -> None:
    """Governed metric columns do not match DataValidator's name heuristics."""
    report = get_validation_service().validate_rows(
        [{"Country": "United States", "Revenue": 12642905.0}]
    )

    skipped = " ".join(check.check for check in report.checks_skipped)
    assert "discount" in skipped.lower()
    assert "sales" in skipped.lower()
    assert any("checks_skipped" in note or "skipped" in note for note in report.notes)
    # The check that genuinely ran is reported as applied, and nothing more.
    assert any("row count" in check for check in report.checks_applied)


def test_data_validation_applies_the_heuristics_when_they_can_match() -> None:
    """Cube-style member names are the input shape DataValidator documents."""
    report = get_validation_service().validate_rows(
        [{"Sales.Sales": 1500.50, "Sales.Discount": 1.75}],
        columns=["Sales.Sales", "Sales.Discount"],
    )

    assert report.data_validation is not None
    assert report.data_validation.invalid_discount_detected is True
    assert report.status == "FLAGGED"
    assert any("discount bounds" in check for check in report.checks_applied)


def test_empty_rows_are_reported_as_a_failure_with_the_skipped_checks() -> None:
    report = get_validation_service().validate_rows([])

    assert report.is_valid is False
    assert report.status == "FAIL"
    assert report.data_validation is not None
    assert report.data_validation.reason
    assert report.checks_skipped


def test_combine_reports_the_weaker_of_the_two_reports() -> None:
    service = get_validation_service()
    passing = service.validate_governed_query(GovernedQuery(measures=["Revenue"]))
    failing = service.validate_rows([])

    combined = service.combine(passing, failing)

    assert combined.is_valid is False
    # FAIL when the validators ran; ERROR if the validator module could not load.
    assert combined.status in {"FAIL", "ERROR"}
    assert combined.schema_validation is not None
    assert combined.data_validation is not None


# ===========================================================================
# The validation endpoints
# ===========================================================================
def test_validate_query_accepts_a_governed_payload(client: TestClient) -> None:
    response = client.post(
        "/api/v1/validate/query",
        json={"payload": {"measures": ["Revenue"], "dimensions": ["Country"]}},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["report"]["status"] in {"PASS", "ERROR"}
    if body["report"]["status"] == "PASS":
        assert "SUM(f.SALES)" in body["compiled_sql_preview"]


def test_validate_query_rejects_an_ungoverned_measure(client: TestClient) -> None:
    response = client.post(
        "/api/v1/validate/query", json={"payload": {"measures": ["Gross Margin"]}}
    )

    assert response.status_code == 200
    body = response.json()

    assert body["report"]["is_valid"] is False
    assert body["compiled_sql_preview"] is None


def test_validate_query_rejects_a_payload_with_no_measures(client: TestClient) -> None:
    response = client.post("/api/v1/validate/query", json={"payload": {"measures": []}})

    assert response.status_code == 200
    assert response.json()["report"]["is_valid"] is False


def test_validate_query_rejects_extra_fields(client: TestClient) -> None:
    response = client.post(
        "/api/v1/validate/query",
        json={"payload": {"measures": ["Revenue"]}, "sql": "SELECT 1"},
    )

    assert response.status_code == 422


def test_validate_data_audits_the_supplied_rows(client: TestClient) -> None:
    response = client.post(
        "/api/v1/validate/data",
        json={"data": [{"Sales.Sales": 100.0, "Sales.Discount": 0.2}]},
    )

    assert response.status_code == 200
    report = response.json()["report"]

    assert report["status"] == "PASS"
    assert report["data_validation"]["row_count"] == 1
    assert report["is_valid"] is True


def test_validate_data_flags_an_out_of_range_discount(client: TestClient) -> None:
    response = client.post(
        "/api/v1/validate/data",
        json={"data": [{"Sales.Sales": 100.0, "Sales.Discount": 4.0}]},
    )

    report = response.json()["report"]

    assert report["data_validation"]["invalid_discount_detected"] is True
    assert report["status"] == "FLAGGED"


def test_validate_data_rejects_an_empty_row_list(client: TestClient) -> None:
    response = client.post("/api/v1/validate/data", json={"data": []})

    assert response.status_code == 200
    report = response.json()["report"]

    assert report["status"] == "FAIL"
    assert report["errors"]


def test_validate_data_rejects_a_sql_field(client: TestClient) -> None:
    response = client.post(
        "/api/v1/validate/data",
        json={"data": [], "sql": "SELECT * FROM fact_sales"},
    )

    assert response.status_code == 422
