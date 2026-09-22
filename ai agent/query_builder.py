import re

from schema import METRICS, DIMENSIONS, TIME_GRANULARITIES


METRIC_ALIASES = {
    "total sales": "Sales",
    "average order value": "Average Order Value",
    "average sales": "Average Order Value",
    "avg sales": "Average Order Value",
    "profit margin": "Profit Margin",
    "quantity sold": "Quantity Sold",
    "units sold": "Quantity Sold",
    "shipping cost": "Shipping Cost",
    "order count": "Orders",
    "number of orders": "Orders",
    "unique customers": "Customers",
    "sales": "Sales",
    "revenue": "Revenue",
    "profit": "Profit",
    "margin": "Profit Margin",
    "orders": "Orders",
    "customers": "Customers",
    "quantity": "Quantity",
    "shipping": "Shipping Cost",
    "aov": "Average Order Value",
}


def identify_metric(question):
    question_lower = question.lower()

    # Check longer aliases first so phrases such as
    # "profit margin" are detected before "profit".
    for alias in sorted(
        METRIC_ALIASES,
        key=len,
        reverse=True,
    ):
        if alias in question_lower:
            return METRIC_ALIASES[alias]

    return None


def identify_dimension(question):
    question_lower = question.lower()

    dimension_aliases = {
        "Year": [
            "year",
            "years",
        ],
        "Country": [
            "country",
            "countries",
        ],
        "Market": [
            "market",
            "markets",
        ],
        "Region": [
            "region",
            "regions",
        ],
        "Category": [
            "category",
            "categories",
        ],
        "Sub-Category": [
            "sub-category",
            "subcategory",
            "sub category",
        ],
        "Product Name": [
            "product name",
            "products",
            "product",
        ],
        "Ship Mode": [
            "ship mode",
            "shipping mode",
        ],
        "Order Priority": [
            "order priority",
            "priority",
        ],
    }

    for dimension, aliases in dimension_aliases.items():
        for alias in aliases:
            if alias in question_lower:
                return dimension

    return None


def identify_time_granularity(question):
    """
    Detect time-series intent separately from normal
    business dimensions.

    Examples:

    "monthly sales trend" -> Month
    "sales by month" -> Month
    "monthly revenue" -> Month
    "quarterly profit" -> Quarter
    "profit by quarter" -> Quarter
    "yearly sales" -> Year
    "sales by year" -> Year
    """

    question_lower = question.lower()

    time_aliases = {
        "Month": [
            "monthly",
            "by month",
            "per month",
            "each month",
            "month over month",
            "month-on-month",
            "mom",
        ],
        "Quarter": [
            "quarterly",
            "by quarter",
            "per quarter",
            "each quarter",
            "quarter over quarter",
            "quarter-on-quarter",
            "qoq",
        ],
        "Year": [
            "yearly",
            "annually",
            "annual",
            "by year",
            "per year",
            "each year",
            "year over year",
            "year-on-year",
            "yoy",
        ],
    }

    for granularity, aliases in time_aliases.items():
        for alias in aliases:
            if alias in question_lower:
                return granularity

    return None


def identify_year(question):
    match = re.search(
        r"\b(20\d{2})\b",
        question,
    )

    if match:
        return int(match.group(1))

    return None


def identify_market(question):
    question_lower = question.lower()

    # Europe is represented by the EU market
    # in the MetricMind semantic layer.
    if any(
        phrase in question_lower
        for phrase in [
            "european",
            "europe",
        ]
    ):
        return "EU"

    return None


def identify_operation(question):
    question_lower = question.lower()

    if any(
        word in question_lower
        for word in [
            "highest",
            "maximum",
            "most",
            "top",
            "best",
        ]
    ):
        return "highest"

    if any(
        word in question_lower
        for word in [
            "lowest",
            "minimum",
            "least",
            "bottom",
            "low",
        ]
    ):
        return "lowest"

    if any(
        word in question_lower
        for word in [
            "compare",
            "comparison",
        ]
    ):
        return "compare"

    if any(
        word in question_lower
        for word in [
            "total",
            "sum",
        ]
    ):
        return "total"

    return None


def identify_time_operation(question):
    """
    Time-series questions such as "monthly sales trend"
    need an aggregation operation, but the user is not
    asking for highest/lowest/compare.

    Therefore a time-series query defaults to total.
    """

    time_granularity = identify_time_granularity(
        question
    )

    if time_granularity is None:
        return None

    operation = identify_operation(question)

    # Explicit ranking/comparison operations remain unchanged.
    if operation is not None:
        return operation

    return "total"


def detect_root_cause_intent(question):
    """
    Detect questions that require a secondary investigation.

    These questions should not be answered from a single
    metric alone. The agent should first inspect the primary
    metric and then investigate an available cost driver.

    Current governed secondary cost driver:
    Shipping Cost

    Material Cost is intentionally not included because it
    is not currently part of the governed MetricMind schema.
    """

    question_lower = question.lower()

    root_cause_phrases = [
        "why did",
        "why has",
        "why have",
        "why is",
        "why are",
        "reason for",
        "reason behind",
        "root cause",
        "cause of",
        "what caused",
        "what is causing",
        "explain the drop",
        "explain the decline",
        "explain the decrease",
        "explain the fall",
        "what drove",
        "what is driving",
    ]

    margin_terms = [
        "margin",
        "profit margin",
    ]

    decline_terms = [
        "drop",
        "decline",
        "decrease",
        "fall",
        "fallen",
        "dropped",
        "decreased",
        "lower",
        "down",
    ]

    has_root_cause_phrase = any(
        phrase in question_lower
        for phrase in root_cause_phrases
    )

    has_margin_term = any(
        term in question_lower
        for term in margin_terms
    )

    has_decline_term = any(
        term in question_lower
        for term in decline_terms
    )

    # Explicit root-cause questions are always treated
    # as multi-step analysis.
    if has_root_cause_phrase and (
        has_margin_term
        or has_decline_term
    ):
        return True

    # "margin dropped" / "profit margin decreased"
    # should also trigger root-cause analysis.
    if has_margin_term and has_decline_term:
        return True

    return False


def build_root_cause_plan(question):
    """
    Build a deterministic secondary-analysis plan.

    The plan describes what the agent should investigate
    after the primary metric has been retrieved.
    """

    return {
        "enabled": True,
        "primary_metric": "Profit Margin",
        "secondary_metrics": [
            "Shipping Cost",
        ],
        "reason": (
            "Investigate available governed cost drivers "
            "after evaluating profit margin."
        ),
    }


def detect_ambiguity(question):
    question_lower = question.lower()

    ambiguous_terms = {
        "best": [
            "Sales",
            "Profit",
            "Quantity",
        ],
        "good": [
            "Sales",
            "Profit",
            "Quantity",
        ],
        "successful": [
            "Sales",
            "Profit",
            "Quantity",
        ],
    }

    for term, possible_metrics in ambiguous_terms.items():

        if term in question_lower:

            if identify_metric(question) is None:

                return {
                    "ambiguous": True,
                    "reason": (
                        f"'{term}' does not specify "
                        "which metric should be used."
                    ),
                    "possible_metrics": possible_metrics,
                }

    return {
        "ambiguous": False,
        "reason": None,
        "possible_metrics": [],
    }


def build_query(question):
    """
    Convert a natural-language business question into
    a structured agent query.

    No raw SQL is generated here.

    The query can contain either:
    - a normal business dimension, such as Country or Category
    - a time granularity, such as Month or Quarter
    - a root-cause analysis plan for multi-step questions

    Time granularity is kept separate because the semantic
    layer handles it through a Cube time dimension.
    """

    metric = identify_metric(question)

    dimension = identify_dimension(question)

    time_granularity = identify_time_granularity(
        question
    )

    # If the question is clearly asking for a time series,
    # "Year" should be represented as a time granularity
    # rather than as an ordinary categorical dimension.
    if time_granularity is not None:

        if dimension == "Year":
            dimension = None

    operation = identify_time_operation(
        question
    )

    root_cause = detect_root_cause_intent(
        question
    )

    root_cause_plan = None

    if root_cause:
        root_cause_plan = build_root_cause_plan(
            question
        )

        # A root-cause question about margin should use
        # Profit Margin as the primary metric even if the
        # user did not explicitly say "profit margin".
        if (
            metric is None
            and (
                "margin" in question.lower()
                or "profit" in question.lower()
            )
        ):
            metric = "Profit Margin"

    return {
        "question": question,
        "metric": metric,
        "dimension": dimension,
        "time_granularity": time_granularity,
        "filters": {
            "Year": identify_year(question),
            "Market": identify_market(question),
        },
        "operation": operation,
        "root_cause": root_cause,
        "root_cause_plan": root_cause_plan,
        "ambiguity": detect_ambiguity(question),
    }