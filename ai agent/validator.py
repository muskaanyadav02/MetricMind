from schema import METRICS, DIMENSIONS


VALID_OPERATIONS = [
    "highest",
    "lowest",
    "average",
    "total",
    "compare",
    None
]


def validate_query(query):
    errors = []

    # Check metric
    if query["metric"] is None:
        errors.append("Metric is missing or unsupported.")
    elif query["metric"] not in METRICS:
        errors.append(f"Unsupported metric: {query['metric']}")

    # Check dimension
    if query["dimension"] is None:
        errors.append("Dimension is missing or unsupported.")
    elif query["dimension"] not in DIMENSIONS:
        errors.append(f"Unsupported dimension: {query['dimension']}")

    # Check operation
    if query["operation"] not in VALID_OPERATIONS:
        errors.append(f"Unsupported operation: {query['operation']}")

    # Check year
    year = query["filters"].get("Year")

    if year is not None and (year < 2000 or year > 2100):
        errors.append(f"Invalid year: {year}")

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }