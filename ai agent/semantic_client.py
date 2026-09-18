import json
import os

import jwt
import requests


CUBE_API_URL = os.getenv(
    "CUBE_API_URL",
    "http://localhost:4000/cubejs-api/v1/load"
)

CUBE_API_SECRET = os.getenv(
    "CUBE_API_SECRET",
    "metricmind-local-development-secret-2026"
)


METRIC_MAP = {
    "Sales": "FactSales.revenue",
    "Revenue": "FactSales.revenue",
    "Profit": "FactSales.profit",
    "Quantity": "FactSales.quantitySold",
    "Quantity Sold": "FactSales.quantitySold",
    "Shipping Cost": "FactSales.shippingCost",
    "Orders": "FactSales.orders",
    "Customers": "FactSales.customers",
    "Profit Margin": "FactSales.profitMargin",
    "Average Order Value": "FactSales.averageOrderValue",
}


DIMENSION_MAP = {
    "Country": "FactSales.country",
    "Region": "FactSales.region",
    "Market": "FactSales.market",
    "Category": "FactSales.category",
    "Sub-Category": "FactSales.subCategory",
    "Product Name": "FactSales.productName",
    "Ship Mode": "FactSales.shipMode",
    "Order Priority": "FactSales.orderPriority",
}


def _create_token():
    """Create a JWT token for the local Cube API."""

    return jwt.encode(
        {},
        CUBE_API_SECRET,
        algorithm="HS256",
    )


def _build_cube_query(structured_query):
    """Convert the AI agent query into a Cube REST query."""

    metric = structured_query.get("metric")
    dimension = structured_query.get("dimension")
    operation = structured_query.get("operation")
    filters = structured_query.get("filters", {})

    # Validate metric.
    if metric not in METRIC_MAP:
        raise ValueError(f"Unsupported metric: {metric}")

    # Dimension is optional for aggregate queries such as:
    # "Show me European sales"
    if dimension is not None and dimension not in DIMENSION_MAP:
        raise ValueError(f"Unsupported dimension: {dimension}")

    measure = METRIC_MAP[metric]

    # Only look up the Cube dimension when one exists.
    cube_dimension = (
        DIMENSION_MAP[dimension]
        if dimension is not None
        else None
    )

    query = {
        "measures": [measure],
        "dimensions": (
            [cube_dimension]
            if cube_dimension is not None
            else []
        ),
        "limit": 10,
    }

    # Convert Year filter into a Cube time dimension.
    if filters.get("Year") is not None:
        year = int(filters["Year"])

        query["timeDimensions"] = [
            {
                "dimension": "FactSales.orderDate",
                "dateRange": [
                    f"{year}-01-01",
                    f"{year}-12-31",
                ],
            }
        ]

    # Convert Market filter into a Cube filter.
    if filters.get("Market") is not None:
        query["filters"] = [
            {
                "member": "FactSales.market",
                "operator": "equals",
                "values": [filters["Market"]],
            }
        ]

    # Highest operation.
    if operation == "highest":
        query["order"] = {
            measure: "desc"
        }
        query["limit"] = 1

    # Lowest operation.
    elif operation == "lowest":
        query["order"] = {
            measure: "asc"
        }
        query["limit"] = 1

    return query


def execute_query(structured_query):
    """
    Send a validated structured query to Cube.

    Returns the Cube API response as a Python dictionary.
    """

    cube_query = _build_cube_query(structured_query)

    token = _create_token()

    headers = {
        "Authorization": token,
    }

    response = requests.get(
        CUBE_API_URL,
        params={
            "query": json.dumps(cube_query)
        },
        headers=headers,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()