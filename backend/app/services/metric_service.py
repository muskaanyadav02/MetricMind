"""The governed metric and dimension registry.

Source of truth
---------------
``docs/metric_dictionary.md`` is the team's governed metric dictionary, so its
eight metrics are the initial registry. Every ``formula`` and ``sql_expression``
below is taken from that document - nothing is invented. Specifically:

* The authoritative summary table (``docs/metric_dictionary.md`` section 2).
* The per-metric formulas (sections 3-10).
* The Metric Governance Rules (section 14, "Rule 1" .. "Rule 8").
* The zero-revenue rule for Profit Margin (section 5): return NULL rather than
  dividing by zero, hence ``NULLIF(SUM(f.SALES), 0)``.
* The non-averaging rule (section 5) and the transaction-grain rule (section 6):
  Orders is ``COUNT(DISTINCT ORDER_ID)``, never a row count.

A conflict this registry does *not* hide
----------------------------------------
The AI agent declares a different metric set in ``ai agent/schema.py``::

    Sales, Profit, Quantity, Discount, Shipping Cost

That overlaps only partially with the governed eight. The differences are
recorded explicitly rather than papered over:

* The agent's ``Sales`` is the governed **Revenue** (``SUM(SALES)``). The alias
  is declared in :data:`AGENT_METRIC_ALIASES` and applied visibly - every
  translation that uses it is reported back in the API response.
* The agent's ``Quantity`` is the governed **Quantity Sold**.
* The agent's ``Discount`` has **no governed equivalent**. It is listed in
  :data:`UNMAPPED_AGENT_METRICS` and requests for it are refused as unsupported
  rather than quietly computed from a raw column.
* **Revenue, Profit Margin, Orders, Customers and Average Order Value are
  unreachable through the current agent**, because it never emits those names.

Replacing this registry
-----------------------
Everything here is plain data plus lookups. When the team's Cube.dev semantic
layer lands, swap :func:`get_metric_service` for a Cube-backed implementation of
:class:`GovernedRegistry`; the API routes and response schemas do not change.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from app.schemas.semantic import DimensionDefinition, MetricDefinition

METRIC_DICTIONARY_DOC = "docs/metric_dictionary.md"
DATA_DICTIONARY_DOC = "docs/data_dictionary.md"
AGENT_SCHEMA_DOC = "ai agent/schema.py"

# Physical source models, as produced by the dbt marts in dbt/metricmind_dbt.
FACT_SALES = "fact_sales"
DIM_PRODUCT = "dim_product"
DIM_CUSTOMER = "dim_customer"
DIM_DATE = "dim_date"

# Table aliases used when compiling SQL.
FACT_ALIAS = "f"
DIM_PRODUCT_ALIAS = "p"
DIM_CUSTOMER_ALIAS = "c"
DIM_DATE_ALIAS = "d"

# The join from the fact to dim_date. fact_sales carries ORDER_DATE (timestamp)
# while dim_date's key is DATE_KEY (date), so the cast is required. This mirrors
# the relationship described in docs/data_dictionary.md.
DIM_DATE_JOIN_CONDITION = f"CAST({FACT_ALIAS}.ORDER_DATE AS DATE) = {DIM_DATE_ALIAS}.DATE_KEY"


def _normalize_key(value: str) -> str:
    """Fold a name for tolerant lookup: case, spaces, hyphens and underscores.

    ``'Sub-Category'``, ``'sub category'`` and ``'Sub_Category'`` all collapse to
    the same key, which is what lets the agent's naming and the governed naming
    meet without special-casing at every call site.
    """
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


# ---------------------------------------------------------------------------
# Governed metrics - docs/metric_dictionary.md
# ---------------------------------------------------------------------------
GOVERNED_METRICS: Tuple[MetricDefinition, ...] = (
    MetricDefinition(
        name="Revenue",
        description="Total sales generated.",
        formula="SUM(SALES)",
        aggregation="SUM",
        additive=True,
        sql_expression=f"SUM({FACT_ALIAS}.SALES)",
        catalog_member="Sales.Revenue",
        source_document=f"{METRIC_DICTIONARY_DOC} (sections 2, 3, 14 Rule 1)",
        aliases=["Sales", "Total Sales", "Revenue"],
        notes="The AI agent calls this metric 'Sales'; the governed name is 'Revenue'.",
    ),
    MetricDefinition(
        name="Profit",
        description="Total profit generated.",
        formula="SUM(PROFIT)",
        aggregation="SUM",
        additive=True,
        sql_expression=f"SUM({FACT_ALIAS}.PROFIT)",
        catalog_member="Sales.Profit",
        source_document=f"{METRIC_DICTIONARY_DOC} (sections 2, 4, 14 Rule 2)",
        aliases=["Profit"],
        notes="Profit can legitimately be negative for individual groups.",
    ),
    MetricDefinition(
        name="Profit Margin",
        description="Profit as a percentage of revenue.",
        formula="SUM(PROFIT) / SUM(SALES) x 100",
        aggregation="ratio",
        additive=False,
        # NULLIF implements the dictionary's zero-revenue rule: NULL, not a
        # division-by-zero error.
        sql_expression=(
            f"SUM({FACT_ALIAS}.PROFIT) / NULLIF(SUM({FACT_ALIAS}.SALES), 0) * 100"
        ),
        catalog_member="Sales.ProfitMargin",
        source_document=f"{METRIC_DICTIONARY_DOC} (sections 2, 5, 14 Rule 3)",
        aliases=["Profit Margin", "Margin", "ProfitMargin"],
        notes=(
            "Non-additive: must be recomputed from aggregated profit and sales, never "
            "averaged from transaction-level PROFIT_MARGIN_PERCENT. Returns NULL when "
            "total revenue is zero."
        ),
    ),
    MetricDefinition(
        name="Orders",
        description="Number of unique orders.",
        formula="COUNT(DISTINCT ORDER_ID)",
        aggregation="COUNT DISTINCT",
        additive=False,
        sql_expression=f"COUNT(DISTINCT {FACT_ALIAS}.ORDER_ID)",
        catalog_member="Sales.Orders",
        source_document=f"{METRIC_DICTIONARY_DOC} (sections 2, 6, 14 Rule 4)",
        aliases=["Orders", "Order Count", "Number of Orders"],
        notes=(
            "The fact table is at order-line grain, so COUNT(*) is not the number of "
            "orders and COUNT(DISTINCT ...) is not additive across groups."
        ),
    ),
    MetricDefinition(
        name="Customers",
        description="Number of unique customers.",
        formula="COUNT(DISTINCT CUSTOMER_ID)",
        aggregation="COUNT DISTINCT",
        additive=False,
        sql_expression=f"COUNT(DISTINCT {FACT_ALIAS}.CUSTOMER_ID)",
        catalog_member="Sales.Customers",
        source_document=f"{METRIC_DICTIONARY_DOC} (sections 2, 7, 14 Rule 5)",
        aliases=["Customers", "Unique Customers"],
        notes="Counts distinct customers, not customer rows.",
    ),
    MetricDefinition(
        name="Quantity Sold",
        description="Total quantity of products sold.",
        formula="SUM(QUANTITY)",
        aggregation="SUM",
        additive=True,
        sql_expression=f"SUM({FACT_ALIAS}.QUANTITY)",
        catalog_member="Sales.QuantitySold",
        source_document=f"{METRIC_DICTIONARY_DOC} (sections 2, 8, 14 Rule 6)",
        aliases=["Quantity Sold", "Quantity", "Units Sold"],
        notes="The AI agent calls this metric 'Quantity'.",
    ),
    MetricDefinition(
        name="Shipping Cost",
        description="Total shipping cost.",
        formula="SUM(SHIPPING_COST)",
        aggregation="SUM",
        additive=True,
        sql_expression=f"SUM({FACT_ALIAS}.SHIPPING_COST)",
        catalog_member="Sales.ShippingCost",
        source_document=f"{METRIC_DICTIONARY_DOC} (sections 2, 9, 14 Rule 7)",
        aliases=["Shipping Cost", "Shipping"],
        notes=None,
    ),
    MetricDefinition(
        name="Average Order Value",
        description="Average revenue per unique order.",
        formula="SUM(SALES) / COUNT(DISTINCT ORDER_ID)",
        aggregation="ratio",
        additive=False,
        sql_expression=(
            f"SUM({FACT_ALIAS}.SALES) / NULLIF(COUNT(DISTINCT {FACT_ALIAS}.ORDER_ID), 0)"
        ),
        catalog_member="Sales.AverageOrderValue",
        source_document=f"{METRIC_DICTIONARY_DOC} (sections 2, 10, 14 Rule 8)",
        aliases=["Average Order Value", "AOV", "Average Order Value (AOV)"],
        notes="Must divide by unique orders, never by transaction rows.",
    ),
)

# The agent's metric vocabulary -> governed metric names. Applied explicitly and
# reported in the API response; never applied silently.
AGENT_METRIC_ALIASES: Dict[str, str] = {
    "Sales": "Revenue",
    "Profit": "Profit",
    "Quantity": "Quantity Sold",
    "Shipping Cost": "Shipping Cost",
}

# Agent metrics with no governed definition. Requests naming these are refused.
UNMAPPED_AGENT_METRICS: Dict[str, str] = {
    "Discount": (
        "docs/metric_dictionary.md governs no 'Discount' metric. Discount is a column on "
        "the fact table, but the dictionary defines only the eight governed metrics."
    ),
}

METRIC_GOVERNANCE_NOTES: List[str] = [
    f"Registry source: {METRIC_DICTIONARY_DOC} (8 governed metrics).",
    f"The AI agent declares a different set in '{AGENT_SCHEMA_DOC}': "
    "Sales, Profit, Quantity, Discount, Shipping Cost.",
    "The agent's 'Sales' is the governed metric 'Revenue' (both are SUM(SALES)); the "
    "backend applies this rename explicitly and reports it in the response.",
    "The agent's 'Discount' has no governed equivalent and is refused as unsupported.",
    "Revenue, Profit Margin, Orders, Customers and Average Order Value cannot currently "
    "be requested through the agent, because it never emits those metric names.",
]


# ---------------------------------------------------------------------------
# Governed dimensions
# ---------------------------------------------------------------------------
def _dimension(
    name: str,
    description: str,
    column: str,
    source_model: str,
    member: str,
    governed: bool,
    provenance: str,
    *,
    join_key: Optional[str] = None,
    is_time: bool = False,
    is_categorical: bool = False,
    aliases: Optional[Sequence[str]] = None,
) -> DimensionDefinition:
    return DimensionDefinition(
        name=name,
        description=description,
        member=member,
        column=column,
        source_model=source_model,
        join_key=join_key,
        governed=governed,
        provenance=provenance,
        is_time=is_time,
        is_categorical=is_categorical,
        aliases=list(aliases or []),
    )


_GEO_PROVENANCE = f"{METRIC_DICTIONARY_DOC} section 12 (Geographic Filtering)"
_TIME_PROVENANCE = f"{METRIC_DICTIONARY_DOC} section 13 (Time Filtering)"
_CATEGORICAL_PROVENANCE = (
    f"Not listed in {METRIC_DICTIONARY_DOC}; derived from the physical dbt mart columns "
    f"({DATA_DICTIONARY_DOC}) and the approved dimension list in '{AGENT_SCHEMA_DOC}'."
)

GOVERNED_DIMENSIONS: Tuple[DimensionDefinition, ...] = (
    # -- Geographic (governed) -------------------------------------------
    _dimension(
        "Country",
        "Country of the transaction.",
        "COUNTRY",
        FACT_SALES,
        "Sales.Country",
        True,
        _GEO_PROVENANCE,
        is_categorical=True,
    ),
    _dimension(
        "Region",
        "Geographic region. Note that Europe is MARKET = 'EU', not REGION = 'Europe'.",
        "REGION",
        FACT_SALES,
        "Sales.Region",
        True,
        _GEO_PROVENANCE,
        is_categorical=True,
    ),
    _dimension(
        "Market",
        "Market. The governed way to analyse Europe: MARKET = 'EU'.",
        "MARKET",
        FACT_SALES,
        "Sales.Market",
        True,
        _GEO_PROVENANCE,
        is_categorical=True,
    ),
    _dimension(
        "Market2",
        "Secondary market attribute present in the source dataset.",
        "MARKET2",
        FACT_SALES,
        "Sales.Market2",
        True,
        _GEO_PROVENANCE,
        is_categorical=True,
    ),
    _dimension(
        "City",
        "City of the transaction.",
        "CITY",
        FACT_SALES,
        "Sales.City",
        True,
        _GEO_PROVENANCE,
        is_categorical=True,
    ),
    _dimension(
        "State",
        "State of the transaction.",
        "STATE",
        FACT_SALES,
        "Sales.State",
        True,
        _GEO_PROVENANCE,
        is_categorical=True,
    ),
    # -- Time (governed) --------------------------------------------------
    _dimension(
        "Year",
        "Order year.",
        "YEAR",
        FACT_SALES,
        "Sales.Year",
        True,
        f"{_TIME_PROVENANCE}; supplied by the {FACT_SALES}.YEAR column, which dbt derives "
        "from ORDER_DATE (equivalent to dim_date.YEAR).",
        is_time=True,
    ),
    _dimension(
        "Week Number",
        "Week number of the order, carried through from the source dataset.",
        "WEEKNUM",
        FACT_SALES,
        "Sales.WeekNumber",
        True,
        f"{_TIME_PROVENANCE}; supplied by {FACT_SALES}.WEEKNUM, the same source column "
        f"{DIM_DATE}.WEEK_NUMBER renames.",
        is_time=True,
    ),
    _dimension(
        "Quarter",
        "Calendar quarter of the order date.",
        "QUARTER",
        DIM_DATE,
        "Sales.OrderDate.Quarter",
        True,
        f"{_TIME_PROVENANCE}; {DATA_DICTIONARY_DOC} dim_date.",
        join_key="DATE_KEY",
        is_time=True,
    ),
    _dimension(
        "Month",
        "Calendar month number of the order date.",
        "MONTH",
        DIM_DATE,
        "Sales.OrderDate.Month",
        True,
        f"{_TIME_PROVENANCE}; {DATA_DICTIONARY_DOC} dim_date.",
        join_key="DATE_KEY",
        is_time=True,
    ),
    _dimension(
        "Month Name",
        "English month name of the order date.",
        "MONTH_NAME",
        DIM_DATE,
        "Sales.OrderDate.MonthName",
        True,
        f"{_TIME_PROVENANCE}; {DATA_DICTIONARY_DOC} dim_date.",
        join_key="DATE_KEY",
        is_time=True,
        aliases=["MonthName"],
    ),
    _dimension(
        "Day",
        "Day of month of the order date.",
        "DAY",
        DIM_DATE,
        "Sales.OrderDate.Day",
        True,
        f"{_TIME_PROVENANCE}; {DATA_DICTIONARY_DOC} dim_date.",
        join_key="DATE_KEY",
        is_time=True,
    ),
    # -- Categorical (physical columns; NOT governed by the metric dictionary)
    _dimension(
        "Category",
        "Product category.",
        "CATEGORY",
        DIM_PRODUCT,
        "Products.Category",
        False,
        _CATEGORICAL_PROVENANCE,
        join_key="PRODUCT_ID",
        is_categorical=True,
    ),
    _dimension(
        "Sub-Category",
        "Product sub-category.",
        "SUB_CATEGORY",
        DIM_PRODUCT,
        "Products.Sub.Category",
        False,
        _CATEGORICAL_PROVENANCE,
        join_key="PRODUCT_ID",
        is_categorical=True,
        aliases=["Sub Category", "SubCategory"],
    ),
    _dimension(
        "Product Name",
        "Product name.",
        "PRODUCT_NAME",
        DIM_PRODUCT,
        "Products.ProductName",
        False,
        _CATEGORICAL_PROVENANCE,
        join_key="PRODUCT_ID",
        is_categorical=True,
        aliases=["Product", "ProductName"],
    ),
    _dimension(
        "Ship Mode",
        "Shipping mode of the order.",
        "SHIP_MODE",
        FACT_SALES,
        "Sales.ShipMode",
        False,
        _CATEGORICAL_PROVENANCE,
        is_categorical=True,
        aliases=["ShipMode", "Shipping Mode"],
    ),
    _dimension(
        "Order Priority",
        "Order priority.",
        "ORDER_PRIORITY",
        FACT_SALES,
        "Sales.OrderPriority",
        False,
        _CATEGORICAL_PROVENANCE,
        is_categorical=True,
        aliases=["OrderPriority", "Priority"],
    ),
)

DIMENSION_GOVERNANCE_NOTES: List[str] = [
    f"Geographic and time dimensions are governed by {METRIC_DICTIONARY_DOC} "
    "(sections 12 and 13).",
    "Category, Sub-Category, Product Name, Ship Mode and Order Priority are NOT listed in "
    f"{METRIC_DICTIONARY_DOC}. They are exposed because they are real columns in the dbt "
    f"marts and are approved dimensions in '{AGENT_SCHEMA_DOC}'. They are returned with "
    "governed=false so the gap is visible rather than hidden.",
    "Europe is MARKET = 'EU'; REGION is not used for European analysis "
    f"({METRIC_DICTIONARY_DOC} section 12).",
]

# Agent operation vocabulary.
OPERATION_TOTAL = "total"
OPERATION_HIGHEST = "highest"
OPERATION_LOWEST = "lowest"
OPERATION_COMPARE = "compare"
OPERATION_AVERAGE = "average"

SUPPORTED_OPERATIONS: Tuple[str, ...] = (
    OPERATION_TOTAL,
    OPERATION_HIGHEST,
    OPERATION_LOWEST,
    OPERATION_COMPARE,
)

# Operations the agent can emit that the backend will not execute.
UNSUPPORTED_OPERATIONS: Dict[str, str] = {
    OPERATION_AVERAGE: (
        "The governed metric dictionary defines no generic 'average' metric. "
        "Averaging is only meaningful for a governed metric: 'Average Order Value' "
        "is available and is defined as SUM(SALES) / COUNT(DISTINCT ORDER_ID)."
    ),
}


class GovernedRegistry:
    """Lookup layer over the governed metric and dimension definitions."""

    def __init__(
        self,
        metrics: Iterable[MetricDefinition] = GOVERNED_METRICS,
        dimensions: Iterable[DimensionDefinition] = GOVERNED_DIMENSIONS,
    ) -> None:
        self._metrics: Tuple[MetricDefinition, ...] = tuple(metrics)
        self._dimensions: Tuple[DimensionDefinition, ...] = tuple(dimensions)
        self._metric_index = self._build_metric_index()
        self._dimension_index = self._build_dimension_index()

    # -- indexing ---------------------------------------------------------
    def _build_metric_index(self) -> Dict[str, MetricDefinition]:
        index: Dict[str, MetricDefinition] = {}
        for metric in self._metrics:
            for key in (metric.name, *metric.aliases):
                index[_normalize_key(key)] = metric
        return index

    def _build_dimension_index(self) -> Dict[str, DimensionDefinition]:
        index: Dict[str, DimensionDefinition] = {}
        for dimension in self._dimensions:
            for key in (dimension.name, *dimension.aliases):
                index[_normalize_key(key)] = dimension
        return index

    # -- accessors --------------------------------------------------------
    @property
    def metrics(self) -> List[MetricDefinition]:
        return list(self._metrics)

    @property
    def dimensions(self) -> List[DimensionDefinition]:
        return list(self._dimensions)

    @property
    def governed_dimension_count(self) -> int:
        return sum(1 for dimension in self._dimensions if dimension.governed)

    def find_metric(self, name: Optional[str]) -> Optional[MetricDefinition]:
        if not name:
            return None
        return self._metric_index.get(_normalize_key(name))

    def find_dimension(self, name: Optional[str]) -> Optional[DimensionDefinition]:
        if not name:
            return None
        return self._dimension_index.get(_normalize_key(name))

    def find_dimensions(self, names: Iterable[str]) -> List[DimensionDefinition]:
        found: List[DimensionDefinition] = []
        for name in names:
            dimension = self.find_dimension(name)
            if dimension is not None:
                found.append(dimension)
        return found

    def resolve_agent_metric(self, agent_metric: Optional[str]) -> Optional[MetricDefinition]:
        """Resolve a metric name as emitted by the AI agent.

        Explicit alias application only. Unknown or unmapped names return ``None``
        so the caller can report them as unsupported.
        """
        if not agent_metric:
            return None
        if agent_metric in UNMAPPED_AGENT_METRICS:
            return None
        canonical = AGENT_METRIC_ALIASES.get(agent_metric, agent_metric)
        return self.find_metric(canonical)

    def source_models_for(self, dimensions: Sequence[DimensionDefinition]) -> List[str]:
        """Distinct non-fact models that must be joined for these dimensions."""
        models: List[str] = []
        for dimension in dimensions:
            if dimension.source_model != FACT_SALES and dimension.source_model not in models:
                models.append(dimension.source_model)
        return models


_REGISTRY = GovernedRegistry()


def get_metric_service() -> GovernedRegistry:
    """FastAPI dependency returning the governed registry."""
    return _REGISTRY


__all__ = [
    "GovernedRegistry",
    "get_metric_service",
    "GOVERNED_METRICS",
    "GOVERNED_DIMENSIONS",
    "AGENT_METRIC_ALIASES",
    "UNMAPPED_AGENT_METRICS",
    "METRIC_GOVERNANCE_NOTES",
    "DIMENSION_GOVERNANCE_NOTES",
    "SUPPORTED_OPERATIONS",
    "UNSUPPORTED_OPERATIONS",
    "OPERATION_TOTAL",
    "OPERATION_HIGHEST",
    "OPERATION_LOWEST",
    "OPERATION_COMPARE",
    "OPERATION_AVERAGE",
    "FACT_SALES",
    "DIM_PRODUCT",
    "DIM_CUSTOMER",
    "DIM_DATE",
    "FACT_ALIAS",
    "DIM_PRODUCT_ALIAS",
    "DIM_CUSTOMER_ALIAS",
    "DIM_DATE_ALIAS",
    "DIM_DATE_JOIN_CONDITION",
    "METRIC_DICTIONARY_DOC",
    "DATA_DICTIONARY_DOC",
    "AGENT_SCHEMA_DOC",
    "_normalize_key",
]
