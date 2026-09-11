"""Semantic-layer schemas: the governed metric/dimension catalogue and the
governed query contract.

The governed query is expressed in *names* from the governed registry, never in
SQL. A client may only reference metrics and dimensions the backend already
knows about; unknown names are rejected during validation. This is what keeps
raw SQL out of the API surface.
"""

from __future__ import annotations

from typing import List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

FilterOperator = Literal[
    "equals",
    "not_equals",
    "in",
    "not_in",
    "contains",
    "gt",
    "gte",
    "lt",
    "lte",
]

TimeGranularity = Literal["day", "week", "month", "quarter", "year"]

ScalarValue = Union[str, int, float, bool]


class MetricDefinition(BaseModel):
    """A governed business metric, per docs/metric_dictionary.md."""

    name: str = Field(description="Governed metric name, e.g. 'Revenue'.")
    description: str
    formula: str = Field(description="Human-readable formula, quoted from the metric dictionary.")
    aggregation: str = Field(description="Aggregation family, e.g. 'SUM' or 'ratio'.")
    additive: bool = Field(
        description="False for ratio metrics such as Profit Margin, which must never be summed."
    )
    sql_expression: str = Field(
        description="Governed SQL expression compiled against the MART fact table."
    )
    catalog_member: str = Field(
        description="Cube-style member name this metric maps to, e.g. 'Sales.Profit'."
    )
    source_document: str = Field(description="Document that governs this definition.")
    aliases: List[str] = Field(
        default_factory=list,
        description="Accepted alternative names, including names emitted by the AI agent.",
    )
    notes: Optional[str] = Field(default=None, description="Governance caveats.")


class DimensionDefinition(BaseModel):
    """A governed dimension, resolved to a physical column and source model."""

    name: str = Field(description="Governed dimension name, e.g. 'Country'.")
    description: str
    member: str = Field(description="Cube-style member name, e.g. 'Sales.Country'.")
    column: str = Field(description="Physical column name in the source model.")
    source_model: str = Field(
        description="dbt mart that supplies the column: fact_sales, dim_product or dim_customer."
    )
    join_key: Optional[str] = Field(
        default=None, description="Fact column used to join the source model, when not the fact."
    )
    governed: bool = Field(
        description="True when the metric dictionary governs this dimension; False when it is "
        "derived from the approved agent schema and physical dbt columns only."
    )
    provenance: str = Field(description="Where this definition comes from.")
    is_time: bool = False
    is_categorical: bool = False
    aliases: List[str] = Field(default_factory=list)


class MetricCatalogResponse(BaseModel):
    """Response for GET /metrics."""

    metrics: List[MetricDefinition]
    count: int
    source_document: str
    notes: List[str] = Field(default_factory=list)


class DimensionCatalogResponse(BaseModel):
    """Response for GET /dimensions."""

    dimensions: List[DimensionDefinition]
    count: int
    governed_count: int
    notes: List[str] = Field(default_factory=list)


class QueryFilter(BaseModel):
    """A filter on a governed dimension. Values are always bound parameters."""

    model_config = ConfigDict(extra="forbid")

    member: str = Field(description="Governed dimension name, e.g. 'Market'.")
    operator: FilterOperator = "equals"
    values: List[ScalarValue] = Field(default_factory=list)


class TimeDimension(BaseModel):
    """A time dimension, mirroring the Cube.dev contract."""

    model_config = ConfigDict(extra="forbid")

    dimension: str = Field(description="Governed dimension name, e.g. 'Year'.")
    granularity: TimeGranularity


class OrderBy(BaseModel):
    """Ordering instruction referencing a governed measure or dimension."""

    model_config = ConfigDict(extra="forbid")

    member: str
    direction: Literal["asc", "desc"] = "desc"


class GovernedQuery(BaseModel):
    """A query expressed entirely in governed names.

    This mirrors the Cube.dev payload shape (``measures`` / ``dimensions`` /
    ``filters`` / ``timeDimensions``) so a future Cube adapter can consume the
    same structure without changing the API routes.
    """

    model_config = ConfigDict(extra="forbid")

    measures: List[str] = Field(description="Governed metric names to aggregate.")
    dimensions: List[str] = Field(default_factory=list, description="Governed dimension names.")
    filters: List[QueryFilter] = Field(default_factory=list)
    time_dimensions: List[TimeDimension] = Field(default_factory=list)
    order_by: List[OrderBy] = Field(default_factory=list)
    limit: Optional[int] = Field(default=None, ge=1, le=10000)


__all__ = [
    "FilterOperator",
    "TimeGranularity",
    "ScalarValue",
    "MetricDefinition",
    "DimensionDefinition",
    "MetricCatalogResponse",
    "DimensionCatalogResponse",
    "QueryFilter",
    "TimeDimension",
    "OrderBy",
    "GovernedQuery",
]
