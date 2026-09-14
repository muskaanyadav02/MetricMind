import re
from schema import METRICS, DIMENSIONS


METRIC_ALIASES = {
    "sales": "Sales",
    "revenue": "Revenue",
    "total sales": "Sales",
    "profit": "Profit",
    "margin": "Profit Margin",
    "profit margin": "Profit Margin",
    "orders": "Orders",
    "order count": "Orders",
    "number of orders": "Orders",
    "customers": "Customers",
    "unique customers": "Customers",
    "quantity": "Quantity",
    "quantity sold": "Quantity Sold",
    "units sold": "Quantity Sold",
    "shipping cost": "Shipping Cost",
    "shipping": "Shipping Cost",
    "aov": "Average Order Value",
    "average order value": "Average Order Value",
}


def identify_metric(question):
    question_lower = question.lower()

    # Check longer aliases first so that "profit margin"
    # is detected before "profit".
    for alias in sorted(METRIC_ALIASES, key=len, reverse=True):
        if alias in question_lower:
            return METRIC_ALIASES[alias]

    return None


def identify_dimension(question):
    question_lower = question.lower()

    dimension_aliases = {
        "Year": ["year", "years"],
        "Country": ["country", "countries"],
        "Market": ["market", "markets"],
        "Region": ["region", "regions"],
        "Category": ["category", "categories"],
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


def identify_year(question):
    match = re.search(r"\b(20\d{2})\b", question)

    if match:
        return int(match.group(1))

    return None


def identify_operation(question):
    question_lower = question.lower()

    if any(
        word in question_lower
        for word in ["highest", "maximum", "most", "top", "best"]
    ):
        return "highest"

    if any(
        word in question_lower
        for word in ["lowest", "minimum", "least", "bottom"]
    ):
        return "lowest"

    if any(
        word in question_lower
        for word in ["compare", "comparison"]
    ):
        return "compare"

    if any(
        word in question_lower
        for word in ["total", "sum"]
    ):
        return "total"

    return None


def detect_ambiguity(question):
    question_lower = question.lower()

    ambiguous_terms = {
        "best": ["Sales", "Profit", "Quantity"],
        "good": ["Sales", "Profit", "Quantity"],
        "successful": ["Sales", "Profit", "Quantity"],
    }

    for term, possible_metrics in ambiguous_terms.items():
        if term in question_lower:
            if identify_metric(question) is None:
                return {
                    "ambiguous": True,
                    "reason": (
                        f"'{term}' does not specify which metric should be used."
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
    """

    return {
        "question": question,
        "metric": identify_metric(question),
        "dimension": identify_dimension(question),
        "filters": {
            "Year": identify_year(question)
        },
        "operation": identify_operation(question),
        "ambiguity": detect_ambiguity(question),
    }