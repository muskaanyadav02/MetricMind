"""Governed query translation, compilation and execution.

This module holds the two pieces of logic the backend most needs to be honest
about:

1. Translation - translate_agent_output turns the AI agent's output into the
   governed query structure.

2. Compilation - compile_governed_query turns a GovernedQuery into parameterised
   SQL. Identifiers come only from the governed registry and filter values are
   always bound parameters.

The same governed query can also be rendered into a Cube.dev REST payload.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple

from fastapi import Depends
from pydantic import BaseModel, Field

from app.adapters.warehouse import (
    QueryPlan,
    QueryResult,
    WarehouseAdapter,
    get_warehouse,
    qualified_model_name,
    validate_identifier,
)
from app.config import Settings, get_settings
from app.core.errors import ValidationFailedError
from app.core.logging import get_logger
from app.schemas.chat import AmbiguityInfo
from app.schemas.semantic import (
    DimensionDefinition,
    GovernedQuery,
    MetricDefinition,
    OrderBy,
    QueryFilter,
    TimeDimension,
)
from app.services.agent_service import AgentInterpretation
from app.services.metric_service import (
    DIM_CUSTOMER,
    DIM_CUSTOMER_ALIAS,
    DIM_DATE,
    DIM_DATE_ALIAS,
    DIM_DATE_JOIN_CONDITION,
    DIM_PRODUCT,
    DIM_PRODUCT_ALIAS,
    FACT_ALIAS,
    FACT_SALES,
    OPERATION_HIGHEST,
    OPERATION_LOWEST,
    SUPPORTED_OPERATIONS,
    UNMAPPED_AGENT_METRICS,
    UNSUPPORTED_OPERATIONS,
    GovernedRegistry,
    get_metric_service,
)

logger = get_logger(__name__)


_STATUS_OK: Literal["ok"] = "ok"
_STATUS_AMBIGUOUS: Literal["ambiguous"] = "ambiguous"
_STATUS_UNSUPPORTED: Literal["unsupported"] = "unsupported"


_MODEL_ALIASES: Dict[str, str] = {
    FACT_SALES: FACT_ALIAS,
    DIM_PRODUCT: DIM_PRODUCT_ALIAS,
    DIM_CUSTOMER: DIM_CUSTOMER_ALIAS,
    DIM_DATE: DIM_DATE_ALIAS,
}


_JOIN_CONDITIONS: Dict[str, str] = {
    DIM_PRODUCT: (
        f"{FACT_ALIAS}.PRODUCT_ID = {DIM_PRODUCT_ALIAS}.PRODUCT_ID"
    ),
    DIM_CUSTOMER: (
        f"{FACT_ALIAS}.CUSTOMER_ID = {DIM_CUSTOMER_ALIAS}.CUSTOMER_ID"
    ),
    DIM_DATE: DIM_DATE_JOIN_CONDITION,
}


_COMPARISON_OPERATORS: Dict[str, str] = {
    "equals": "=",
    "not_equals": "<>",
    "gt": ">",
    "gte": ">=",
    "lt": "<",
    "lte": "<=",
}


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------


class TranslationOutcome(BaseModel):
    """Result of translating the agent's output into a governed query."""

    status: Literal["ok", "ambiguous", "unsupported"]

    governed_query: Optional[GovernedQuery] = None

    message: Optional[str] = None

    notes: List[str] = Field(
        default_factory=list
    )

    ambiguity: AmbiguityInfo = Field(
        default_factory=AmbiguityInfo
    )


def _unsupported(
    message: str,
    notes: Sequence[str],
    ambiguity: AmbiguityInfo,
) -> TranslationOutcome:
    return TranslationOutcome(
        status=_STATUS_UNSUPPORTED,
        message=message,
        notes=list(notes),
        ambiguity=ambiguity,
    )


def translate_agent_output(
    interpretation: AgentInterpretation,
    registry: GovernedRegistry,
    *,
    default_limit: int,
    max_limit: int,
) -> TranslationOutcome:
    """Translate the AI agent's output into a governed query.

    If the agent output cannot be mapped onto governed metrics and dimensions,
    the result is ambiguous or unsupported instead of inventing a query.
    """

    notes: List[str] = []
    ambiguity = interpretation.ambiguity

    # ------------------------------------------------------------------
    # 1. Agent ambiguity
    # ------------------------------------------------------------------

    if ambiguity.ambiguous:
        reason = (
            ambiguity.reason
            or "The question does not identify a single metric."
        )

        notes.append(
            "The AI agent reported the question as ambiguous; "
            "no query was generated."
        )

        return TranslationOutcome(
            status=_STATUS_AMBIGUOUS,
            message=f"{reason} Please name the metric explicitly.",
            notes=notes,
            ambiguity=ambiguity,
        )

    # ------------------------------------------------------------------
    # 2. Metric is mandatory
    # ------------------------------------------------------------------

    if not interpretation.metric:
        notes.append(
            "The AI agent did not identify any governed metric "
            "in the question."
        )

        return _unsupported(
            "No governed metric was identified in the question. "
            "The governed metrics are available from GET /api/v1/metrics.",
            notes,
            ambiguity,
        )

    if interpretation.metric in UNMAPPED_AGENT_METRICS:
        reason = UNMAPPED_AGENT_METRICS[interpretation.metric]

        notes.append(
            f"The agent named '{interpretation.metric}', "
            "which has no governed definition."
        )

        return _unsupported(
            f"'{interpretation.metric}' is not a governed metric. "
            f"{reason}",
            notes,
            ambiguity,
        )

    metric = registry.resolve_agent_metric(
        interpretation.metric
    )

    if metric is None:
        notes.append(
            f"The agent named '{interpretation.metric}', "
            "which is not in the governed registry."
        )

        return _unsupported(
            f"'{interpretation.metric}' is not a governed metric. "
            "See GET /api/v1/metrics for the governed metric list.",
            notes,
            ambiguity,
        )

    if metric.name != interpretation.metric:
        notes.append(
            f"Agent metric '{interpretation.metric}' was interpreted "
            f"as the governed metric '{metric.name}' "
            f"({metric.formula})."
        )

    # ------------------------------------------------------------------
    # 3. Dimension is optional
    # ------------------------------------------------------------------

    dimension: Optional[DimensionDefinition] = None

    if interpretation.dimension:
        dimension = registry.find_dimension(
            interpretation.dimension
        )

        if dimension is None:
            notes.append(
                f"The agent named dimension "
                f"'{interpretation.dimension}', "
                "which is not governed."
            )

            return _unsupported(
                f"'{interpretation.dimension}' is not a governed "
                "dimension. See GET /api/v1/dimensions for the "
                "governed dimension list.",
                notes,
                ambiguity,
            )

        if dimension.name != interpretation.dimension:
            notes.append(
                f"Agent dimension '{interpretation.dimension}' "
                f"was interpreted as the governed dimension "
                f"'{dimension.name}' "
                f"({dimension.source_model}.{dimension.column})."
            )

        if not dimension.governed:
            notes.append(
                f"'{dimension.name}' is exposed from the physical "
                "dbt mart but is not listed in the governed metric "
                "dictionary; treat its values as ungoverned."
            )

    # ------------------------------------------------------------------
    # 4. Operation
    # ------------------------------------------------------------------

    operation = interpretation.operation

    if operation in UNSUPPORTED_OPERATIONS:
        reason = UNSUPPORTED_OPERATIONS[operation]

        notes.append(
            f"The agent operation '{operation}' "
            "has no governed execution."
        )

        return _unsupported(
            f"The operation '{operation}' is not supported. "
            f"{reason}",
            notes,
            ambiguity,
        )

    if (
        operation is not None
        and operation not in SUPPORTED_OPERATIONS
    ):
        notes.append(
            f"The agent returned an unrecognised operation "
            f"'{operation}'."
        )

        return _unsupported(
            f"The operation '{operation}' is not supported.",
            notes,
            ambiguity,
        )

    # ------------------------------------------------------------------
    # 5. Assemble governed query
    # ------------------------------------------------------------------

    measures = [metric.name]

    dimensions = (
        [dimension.name]
        if dimension
        else []
    )

    filters: List[QueryFilter] = []

    # ------------------------------------------------------------------
    # Year filter
    # ------------------------------------------------------------------

    if interpretation.year is not None:
        filters.append(
            QueryFilter(
                member="Year",
                operator="equals",
                values=[interpretation.year],
            )
        )

        notes.append(
            f"Agent year filter {interpretation.year} was applied "
            "to the governed 'Year' dimension "
            "(fact_sales.YEAR)."
        )

    # ------------------------------------------------------------------
    # Market filter
    # ------------------------------------------------------------------

    if interpretation.market is not None:
        filters.append(
            QueryFilter(
                member="Market",
                operator="equals",
                values=[interpretation.market],
            )
        )

        notes.append(
            f"Agent market filter '{interpretation.market}' "
            "was applied to the governed 'Market' dimension "
            "(fact_sales.MARKET)."
        )

    # ------------------------------------------------------------------
    # Time-series dimensions
    #
    # Agent output:
    #
    #     Month
    #     Quarter
    #     Year
    #
    # Cube representation:
    #
    #     FactSales.orderDate + month
    #     FactSales.orderDate + quarter
    #     FactSales.orderDate + year
    # ------------------------------------------------------------------

    time_dimensions: List[TimeDimension] = []

    if interpretation.time_granularity:
        granularity_map = {
            "Month": "month",
            "Quarter": "quarter",
            "Year": "year",
        }

        granularity = granularity_map.get(
            interpretation.time_granularity
        )

        if granularity is None:
            return _unsupported(
                f"Unsupported time granularity "
                f"'{interpretation.time_granularity}'.",
                notes,
                ambiguity,
            )

        time_dimensions.append(
            TimeDimension(
                dimension="FactSales.orderDate",
                granularity=granularity,
            )
        )

        notes.append(
            f"Agent time granularity "
            f"'{interpretation.time_granularity}' was translated "
            f"to Cube granularity '{granularity}' using "
            "FactSales.orderDate."
        )

    # ------------------------------------------------------------------
    # Ordering
    # ------------------------------------------------------------------

    order_by: List[OrderBy] = []

    # Time-series results must remain chronological.
    if time_dimensions:
        pass

    elif (
        dimension
        and operation == OPERATION_HIGHEST
    ):
        order_by.append(
            OrderBy(
                member=metric.name,
                direction="desc",
            )
        )

        notes.append(
            f"Operation 'highest' was translated into "
            f"ORDER BY {metric.name} DESC."
        )

    elif (
        dimension
        and operation == OPERATION_LOWEST
    ):
        order_by.append(
            OrderBy(
                member=metric.name,
                direction="asc",
            )
        )

        notes.append(
            f"Operation 'lowest' was translated into "
            f"ORDER BY {metric.name} ASC."
        )

    elif dimension:
        order_by.append(
            OrderBy(
                member=metric.name,
                direction="desc",
            )
        )

        notes.append(
            f"Results ordered by {metric.name} DESC "
            "for a deterministic row limit."
        )

    # ------------------------------------------------------------------
    # Result limit
    # ------------------------------------------------------------------

    if time_dimensions:
        query_limit = min(
            1000,
            max_limit,
        )

        notes.append(
            "Time-series query limit increased to support "
            "monthly, quarterly, or yearly result sets."
        )

    else:
        query_limit = min(
            default_limit,
            max_limit,
        )

    notes.append(
        "Answer text is generated deterministically from the "
        "returned rows; no language model is invoked by the "
        "current agent implementation."
    )

    governed_query = GovernedQuery(
        measures=measures,
        dimensions=dimensions,
        filters=filters,
        time_dimensions=time_dimensions,
        order_by=order_by,
        limit=(
            1
            if (
                dimension
                and operation in {
                    OPERATION_HIGHEST,
                    OPERATION_LOWEST,
                }
            )
            else query_limit
        ),
    )

    return TranslationOutcome(
        status=_STATUS_OK,
        governed_query=governed_query,
        notes=notes,
        ambiguity=ambiguity,
    )


# ---------------------------------------------------------------------------
# Compilation
# ---------------------------------------------------------------------------


def _resolve_measures(
    names: Sequence[str],
    registry: GovernedRegistry,
) -> List[MetricDefinition]:
    resolved: List[MetricDefinition] = []

    for name in names:
        metric = registry.find_metric(name)

        if metric is None:
            raise ValidationFailedError(
                f"'{name}' is not a governed metric.",
                details=[
                    {
                        "field": "measures",
                        "message": (
                            f"Unknown metric '{name}'."
                        ),
                    }
                ],
            )

        resolved.append(metric)

    return resolved


def _resolve_dimensions(
    names: Sequence[str],
    registry: GovernedRegistry,
) -> List[DimensionDefinition]:
    resolved: List[DimensionDefinition] = []

    for name in names:
        dimension = registry.find_dimension(name)

        if dimension is None:
            raise ValidationFailedError(
                f"'{name}' is not a governed dimension.",
                details=[
                    {
                        "field": "dimensions",
                        "message": (
                            f"Unknown dimension '{name}'."
                        ),
                    }
                ],
            )

        resolved.append(dimension)

    return resolved


def _column_expression(
    dimension: DimensionDefinition,
) -> str:
    alias = _MODEL_ALIASES[dimension.source_model]

    return (
        f"{alias}."
        f"{validate_identifier(dimension.column)}"
    )


def _build_where_clause(
    filters: Sequence[QueryFilter],
    registry: GovernedRegistry,
) -> Tuple[List[str], List[Any]]:
    """Compile filters into SQL predicates and bound parameters."""

    clauses: List[str] = []
    parameters: List[Any] = []

    for query_filter in filters:
        dimension = registry.find_dimension(
            query_filter.member
        )

        if dimension is None:
            raise ValidationFailedError(
                f"Filter member '{query_filter.member}' "
                "is not a governed dimension.",
                details=[
                    {
                        "field": "filters",
                        "message": (
                            f"Unknown dimension "
                            f"'{query_filter.member}'."
                        ),
                    }
                ],
            )

        column = _column_expression(dimension)

        values = list(
            query_filter.values
        )

        operator = query_filter.operator

        if operator in (
            "in",
            "not_in",
        ):
            if not values:
                raise ValidationFailedError(
                    f"Filter on '{dimension.name}' "
                    "requires at least one value."
                )

            placeholders = ", ".join(
                ["%s"] * len(values)
            )

            keyword = (
                "IN"
                if operator == "in"
                else "NOT IN"
            )

            clauses.append(
                f"{column} {keyword} "
                f"({placeholders})"
            )

            parameters.extend(values)

            continue

        if not values:
            raise ValidationFailedError(
                f"Filter on '{dimension.name}' "
                "requires a value."
            )

        value = values[0]

        if operator == "contains":
            clauses.append(
                f"{column} ILIKE %s"
            )

            parameters.append(
                f"%{value}%"
            )

            continue

        sql_operator = _COMPARISON_OPERATORS.get(
            operator
        )

        if sql_operator is None:
            raise ValidationFailedError(
                f"Unsupported filter operator "
                f"'{operator}'."
            )

        clauses.append(
            f"{column} {sql_operator} %s"
        )

        parameters.append(value)

    return clauses, parameters


def _order_expression(
    order: OrderBy,
    metrics: Sequence[MetricDefinition],
    dimensions: Sequence[DimensionDefinition],
    registry: GovernedRegistry,
) -> Optional[str]:

    for metric in metrics:
        if metric.name == order.member:
            return metric.sql_expression

    for dimension in dimensions:
        if dimension.name == order.member:
            return _column_expression(
                dimension
            )

    metric = registry.find_metric(
        order.member
    )

    if metric is not None:
        return metric.sql_expression

    dimension = registry.find_dimension(
        order.member
    )

    if dimension is not None:
        return _column_expression(
            dimension
        )

    return None


def compile_governed_query(
    governed_query: GovernedQuery,
    registry: GovernedRegistry,
    settings: Settings,
) -> QueryPlan:
    """Compile a governed query into a parameterised QueryPlan."""

    if not governed_query.measures:
        raise ValidationFailedError(
            "At least one governed measure is required.",
            details=[
                {
                    "field": "measures",
                    "message": (
                        "This field is required "
                        "and must not be empty."
                    ),
                }
            ],
        )

    metrics = _resolve_measures(
        governed_query.measures,
        registry,
    )

    dimensions = _resolve_dimensions(
        governed_query.dimensions,
        registry,
    )

    select_parts: List[str] = []
    columns: List[str] = []

    # ------------------------------------------------------------------
    # Dimensions
    # ------------------------------------------------------------------

    for dimension in dimensions:
        expression = _column_expression(
            dimension
        )

        select_parts.append(
            f'{expression} AS "{dimension.name}"'
        )

        columns.append(
            dimension.name
        )

    # ------------------------------------------------------------------
    # Time dimensions
    # ------------------------------------------------------------------

    time_group_by_parts: List[str] = []

    for time_dimension in governed_query.time_dimensions:
        if time_dimension.dimension != "FactSales.orderDate":
            raise ValidationFailedError(
                f"Unsupported time dimension "
                f"'{time_dimension.dimension}'.",
                details=[
                    {
                        "field": "time_dimensions",
                        "message": (
                            "Only FactSales.orderDate "
                            "is supported for time-series queries."
                        ),
                    }
                ],
            )

        granularity = time_dimension.granularity

        if granularity == "year":
            expression = (
                f"EXTRACT(YEAR FROM "
                f"{FACT_ALIAS}.ORDER_DATE)"
            )
            column_name = "Year"

        elif granularity == "quarter":
            expression = (
                f"DATE_TRUNC('QUARTER', "
                f"{FACT_ALIAS}.ORDER_DATE)"
            )
            column_name = "Quarter"

        elif granularity == "month":
            expression = (
                f"DATE_TRUNC('MONTH', "
                f"{FACT_ALIAS}.ORDER_DATE)"
            )
            column_name = "Month"

        elif granularity == "week":
            expression = (
                f"DATE_TRUNC('WEEK', "
                f"{FACT_ALIAS}.ORDER_DATE)"
            )
            column_name = "Week"

        elif granularity == "day":
            expression = (
                f"DATE_TRUNC('DAY', "
                f"{FACT_ALIAS}.ORDER_DATE)"
            )
            column_name = "Day"

        else:
            raise ValidationFailedError(
                f"Unsupported time granularity "
                f"'{granularity}'.",
                details=[
                    {
                        "field": "time_dimensions",
                        "message": (
                            f"Unsupported granularity "
                            f"'{granularity}'."
                        ),
                    }
                ],
            )

        select_parts.append(
            f'{expression} AS "{column_name}"'
        )

        columns.append(
            column_name
        )

        time_group_by_parts.append(
            expression
        )

    # ------------------------------------------------------------------
    # Measures
    # ------------------------------------------------------------------

    for metric in metrics:
        select_parts.append(
            f'{metric.sql_expression} '
            f'AS "{metric.name}"'
        )

        columns.append(
            metric.name
        )

    # ------------------------------------------------------------------
    # FROM clause
    # ------------------------------------------------------------------

    fact_table = qualified_model_name(
        settings,
        FACT_SALES,
    )

    from_clause = [
        f"FROM {fact_table} AS {FACT_ALIAS}"
    ]

    joined_models: List[str] = []

    for dimension in dimensions:
        model = dimension.source_model

        if (
            model == FACT_SALES
            or model in joined_models
        ):
            continue

        if dimension.join_key is not None:
            validate_identifier(
                dimension.join_key
            )

        alias = _MODEL_ALIASES[model]

        table = qualified_model_name(
            settings,
            model,
        )

        condition = _JOIN_CONDITIONS[model]

        from_clause.append(
            f"LEFT JOIN {table} AS {alias} "
            f"ON {condition}"
        )

        joined_models.append(
            model
        )

    # ------------------------------------------------------------------
    # WHERE clause
    # ------------------------------------------------------------------

    where_clauses, parameters = (
        _build_where_clause(
            governed_query.filters,
            registry,
        )
    )

    # ------------------------------------------------------------------
    # GROUP BY
    # ------------------------------------------------------------------

    group_by_parts = [
        _column_expression(dimension)
        for dimension in dimensions
    ]

    # Add time-series grouping.
    group_by_parts.extend(
        time_group_by_parts
    )

    # ------------------------------------------------------------------
    # ORDER BY
    # ------------------------------------------------------------------

    order_parts: List[str] = []

    for order in governed_query.order_by:
        expression = _order_expression(
            order,
            metrics,
            dimensions,
            registry,
        )

        if expression is None:
            raise ValidationFailedError(
                f"Cannot order by '{order.member}': "
                "it is not a governed metric or dimension.",
                details=[
                    {
                        "field": "order_by",
                        "message": (
                            f"Unknown member "
                            f"'{order.member}'."
                        ),
                    }
                ],
            )

        direction = (
            "DESC"
            if order.direction == "desc"
            else "ASC"
        )

        order_parts.append(
            f"{expression} {direction}"
        )

    # Time-series queries should be chronological.
    if time_group_by_parts:
        order_parts.extend(
            f"{expression} ASC"
            for expression in time_group_by_parts
        )

    # ------------------------------------------------------------------
    # LIMIT
    # ------------------------------------------------------------------

    requested_limit = (
        governed_query.limit
        or settings.default_result_rows
    )

    effective_limit = max(
        1,
        min(
            int(requested_limit),
            int(settings.max_result_rows),
        ),
    )

    # ------------------------------------------------------------------
    # SQL assembly
    # ------------------------------------------------------------------

    sql_lines = [
        "SELECT",
        "    "
        + ",\n    ".join(select_parts),
        *from_clause,
    ]

    if where_clauses:
        sql_lines.append(
            "WHERE "
            + " AND ".join(where_clauses)
        )

    if group_by_parts:
        sql_lines.append(
            "GROUP BY "
            + ", ".join(group_by_parts)
        )

    if order_parts:
        sql_lines.append(
            "ORDER BY "
            + ", ".join(order_parts)
        )

    sql_lines.append(
        f"LIMIT {effective_limit}"
    )

    return QueryPlan(
        sql="\n".join(sql_lines),
        parameters=parameters,
        source_model=fact_table,
        columns=columns,
    )
def build_cube_payload(
    governed_query: GovernedQuery,
) -> Dict[str, Any]:
    """Render a governed query in Cube.dev REST payload shape."""

    payload: Dict[str, Any] = {
        "measures": list(
            governed_query.measures
        ),
        "dimensions": list(
            governed_query.dimensions
        ),
        "filters": [
            {
                "member": query_filter.member,
                "operator": query_filter.operator,
                "values": list(
                    query_filter.values
                ),
            }
            for query_filter
            in governed_query.filters
        ],
        "timeDimensions": [
            {
                "dimension": time_dimension.dimension,
                "granularity": (
                    time_dimension.granularity
                ),
            }
            for time_dimension
            in governed_query.time_dimensions
        ],
        "limit": governed_query.limit,
    }

    if governed_query.order_by:
        payload["order"] = [
            {
                "id": order.member,
                "desc": (
                    order.direction == "desc"
                ),
            }
            for order in governed_query.order_by
        ]

    return payload


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


@dataclass
class QueryExecution:
    """A compiled plan together with the rows it produced."""

    plan: QueryPlan
    result: QueryResult


def summarize_result(
    metric_name: Optional[str],
    rows: Sequence[Dict[str, Any]],
    dimensions: Sequence[str],
    operation: Optional[str] = None,
    display_metric_name: Optional[str] = None,
) -> str:
    """Generate deterministic, readable summaries from returned rows.

    ``metric_name`` is the governed result-column name. ``display_metric_name``
    is the metric wording supplied by the agent, when it differs from the
    governed name. All values in the answer come from the returned rows.
    """
    from datetime import date, datetime
    import math

    row_count = len(rows)
    measure = display_metric_name or metric_name or "value"
    operation_normalized = (operation or "").strip().lower()

    highest_operations = {"highest", "maximum", "max", "top", "most"}
    lowest_operations = {"lowest", "minimum", "min", "least"}
    is_highest = operation_normalized in highest_operations
    is_lowest = operation_normalized in lowest_operations

    metric_keys = {
        name.lower()
        for name in (metric_name, display_metric_name)
        if name
    }

    def get_measure_value(row: Dict[str, Any]) -> Any:
        """Read the value from the actual returned metric column."""
        for candidate in (metric_name, display_metric_name):
            if candidate and candidate in row:
                return row[candidate]

        for key, value in row.items():
            if key.lower() in metric_keys:
                return value

        return None

    def numeric_value(row: Dict[str, Any]) -> Optional[float]:
        value = get_measure_value(row)
        if value is None or isinstance(value, bool):
            return None
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        return number if math.isfinite(number) else None

    def format_number(value: Any) -> str:
        if value is None:
            return "N/A"
        if isinstance(value, bool):
            return str(value)
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)
        return f"{number:,.2f}" if math.isfinite(number) else str(value)

    def format_period(value: Any) -> str:
        if isinstance(value, (date, datetime)):
            return value.strftime("%b %Y")
        text = str(value)
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return text
        return parsed.strftime("%b %Y")

    def format_dimension_value(dimension: str, value: Any) -> str:
        if value is None:
            return "N/A"
        if dimension.lower() in {
            "month", "quarter", "year", "week", "day", "date",
            "orderdate", "order_date",
        }:
            return format_period(value)
        return str(value)

    def describe_row(row: Dict[str, Any]) -> str:
        labels = [
            f"{dimension} {format_dimension_value(dimension, row.get(dimension))}"
            for dimension in dimensions
        ]
        return " and ".join(labels) if labels else "the result"

    if not rows:
        return (
            f"No matching records were found for {measure}. "
            "Try adjusting your filters or selecting another period."
        )

    # Highest/lowest must be handled before the single-row branch: governed
    # highest/lowest queries intentionally return only the winning row.
    if dimensions and (is_highest or is_lowest):
        candidates = [row for row in rows if numeric_value(row) is not None]
        if not candidates:
            return (
                f"The query returned results for {measure}, but numeric values "
                "were unavailable for comparison."
            )

        selected_row = (
            max(candidates, key=numeric_value)
            if is_highest
            else min(candidates, key=numeric_value)
        )
        selected_value = format_number(get_measure_value(selected_row))
        dimension_name = dimensions[0].lower()
        item_label = describe_row(selected_row)

        if is_highest:
            return (
                f"The {dimension_name} with the highest {measure.lower()} is "
                f"{item_label}, with {measure.lower()} of {selected_value}."
            )
        return (
            f"The {dimension_name} with the lowest {measure.lower()} is "
            f"{item_label}, with {measure.lower()} of {selected_value}."
        )

    # Grouped results such as profit by category or sales by region.
    if dimensions:
        dimension = dimensions[0]
        valid_rows = [row for row in rows if row.get(dimension) is not None]
        if not valid_rows:
            return (
                f"The query returned {row_count} rows, but no values were "
                f"available for {dimension}."
            )

        numeric_rows = [row for row in valid_rows if numeric_value(row) is not None]
        if not numeric_rows:
            return (
                f"The query returned {row_count} results for {measure}, grouped "
                f"by {dimension}, but numeric values were unavailable for comparison."
            )

        if row_count == 1:
            row = rows[0]
            return (
                f"{measure} for {describe_row(row)}: "
                f"{format_number(get_measure_value(row))}."
            )

        ranked_rows = sorted(numeric_rows, key=numeric_value, reverse=True)
        top_row = ranked_rows[0]
        summary = (
            f"{measure} by {dimension}\n\n"
            f"{describe_row(top_row)} has the highest returned value at "
            f"{format_number(get_measure_value(top_row))}."
        )

        other_rows = ranked_rows[1:4]
        if other_rows:
            other_results = "; ".join(
                f"{describe_row(row)}: {format_number(get_measure_value(row))}"
                for row in other_rows
            )
            summary += f"\n\nOther results: {other_results}."

        summary += f"\n\nA total of {row_count} result rows were returned."
        return summary

    # Time-series queries have no ordinary dimensions but return a period key.
    if row_count > 1:
        first_row = rows[0]
        period_names = {
            "month", "quarter", "year", "week", "day", "date",
            "orderdate", "order_date",
        }
        period_key = next(
            (
                key for key in first_row
                if key.lower() not in metric_keys and key.lower() in period_names
            ),
            None,
        )

        if period_key is None:
            period_key = next(
                (
                    key for key, value in first_row.items()
                    if key.lower() not in metric_keys
                    and (
                        isinstance(value, (date, datetime))
                        or (
                            isinstance(value, str)
                            and len(value) >= 7
                            and value[4:5] == "-"
                        )
                    )
                ),
                None,
            )

        if period_key is not None:
            valid_rows = [
                row for row in rows
                if row.get(period_key) is not None and numeric_value(row) is not None
            ]
            if valid_rows:
                first = valid_rows[0]
                last = valid_rows[-1]
                first_value = numeric_value(first)
                last_value = numeric_value(last)
                first_period = format_dimension_value(period_key, first.get(period_key))
                last_period = format_dimension_value(period_key, last.get(period_key))

                summary = (
                    f"{measure} trend\n\n"
                    f"The query returned {len(valid_rows)} time periods, from "
                    f"{first_period} to {last_period}.\n\n"
                    f"Starting value: {format_number(first_value)} ({first_period})\n"
                    f"Ending value: {format_number(last_value)} ({last_period})"
                )

                if first_value != 0:
                    percentage_change = (
                        (last_value - first_value) / abs(first_value)
                    ) * 100
                    if percentage_change > 0:
                        direction = "increased"
                    elif percentage_change < 0:
                        direction = "decreased"
                    else:
                        direction = "remained unchanged"
                    summary += (
                        f"\n\nOverall change: {measure} {direction} by "
                        f"{abs(percentage_change):,.2f}% between the first "
                        "and last returned periods."
                    )

                peak_row = max(valid_rows, key=numeric_value)
                peak_period = format_dimension_value(
                    period_key, peak_row.get(period_key)
                )
                summary += (
                    f"\n\nHighest returned period: {peak_period}, with "
                    f"{format_number(get_measure_value(peak_row))}."
                )
                return summary

        return (
            f"The query returned {row_count} results for {measure}. "
            "Review the chart to explore the individual values."
        )

    return (
        f"{measure}\n\n"
        f"The returned value is {format_number(get_measure_value(rows[0]))}."
    )

class QueryService:
    """Compiles and executes governed queries against the warehouse."""

    def __init__(
        self,
        warehouse: WarehouseAdapter,
        registry: GovernedRegistry,
        settings: Settings,
    ) -> None:
        self._warehouse = warehouse
        self._registry = registry
        self._settings = settings

    @property
    def registry(
        self,
    ) -> GovernedRegistry:
        return self._registry

    @property
    def warehouse(
        self,
    ) -> WarehouseAdapter:
        return self._warehouse

    def compile(
        self,
        governed_query: GovernedQuery,
    ) -> QueryPlan:
        """Compile without executing.

        The plan carries both renderings of the same governed query:
        parameterised SQL for Snowflake and a Cube.dev payload.
        """

        plan = compile_governed_query(
            governed_query,
            self._registry,
            self._settings,
        )

        return QueryPlan(
            sql=plan.sql,
            parameters=plan.parameters,
            source_model=plan.source_model,
            columns=plan.columns,
            cube_payload=build_cube_payload(
                governed_query
            ),
        )

    def execute(
        self,
        governed_query: GovernedQuery,
    ) -> QueryExecution:
        """Compile and run a governed query."""

        plan = self.compile(
            governed_query
        )

        self._warehouse.require_configured()

        result = self._warehouse.execute(
            plan,
            self._settings.warehouse_timeout_seconds,
        )

        return QueryExecution(
            plan=plan,
            result=result,
        )


def get_query_service(
    warehouse: WarehouseAdapter = Depends(
        get_warehouse
    ),
    registry: GovernedRegistry = Depends(
        get_metric_service
    ),
    settings: Settings = Depends(
        get_settings
    ),
) -> QueryService:
    """FastAPI dependency returning the query service."""

    return QueryService(
        warehouse=warehouse,
        registry=registry,
        settings=settings,
    )


__all__ = [
    "TranslationOutcome",
    "translate_agent_output",
    "compile_governed_query",
    "build_cube_payload",
    "summarize_result",
    "QueryExecution",
    "QueryService",
    "get_query_service",
]