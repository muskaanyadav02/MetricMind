import re
from schema import METRICS, DIMENSIONS


def identify_metric(question):
    question_lower = question.lower()

    for metric in METRICS:
        if metric.lower() in question_lower:
            return metric

    return None


def identify_dimension(question):
    question_lower = question.lower()

    dimension_aliases = {
        "Year": ["year", "years"],
        "Country": ["country", "countries"],
        "Market": ["market", "markets"],
        "Region": ["region", "regions"],
        "Category": ["category", "categories"],
        "Sub-Category": ["sub-category", "subcategory", "sub category"],
        "Product Name": ["product", "products", "product name"],
        "Ship Mode": ["ship mode", "shipping mode"],
        "Order Priority": ["order priority", "priority"]
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

    if any(word in question_lower for word in ["highest", "maximum", "most", "top", "best"]):
        return "highest"

    if any(word in question_lower for word in ["lowest", "minimum", "least", "bottom"]):
        return "lowest"

    if any(word in question_lower for word in ["average", "avg", "mean"]):
        return "average"

    if any(word in question_lower for word in ["total", "sum"]):
        return "total"

    if any(word in question_lower for word in ["compare", "comparison"]):
        return "compare"

    return None


def detect_ambiguity(question):
    question_lower = question.lower()

    ambiguous_terms = {
        "best": ["Sales", "Profit", "Quantity"],
        "good": ["Sales", "Profit", "Quantity"],
        "successful": ["Sales", "Profit", "Quantity"]
    }

    for term, possible_metrics in ambiguous_terms.items():
        if term in question_lower:
            # If a specific metric is already mentioned, it is not ambiguous
            if identify_metric(question) is None:
                return {
                    "ambiguous": True,
                    "reason": f"'{term}' does not specify which metric should be used.",
                    "possible_metrics": possible_metrics
                }

    return {
        "ambiguous": False,
        "reason": None,
        "possible_metrics": []
    }

def build_query(question):
    return {
        "question": question,
        "metric": identify_metric(question),
        "dimension": identify_dimension(question),
        "filters": {
            "Year": identify_year(question)
        },
        "operation": identify_operation(question),
        "ambiguity": detect_ambiguity(question)
    }