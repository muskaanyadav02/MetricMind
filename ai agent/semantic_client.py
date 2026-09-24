import json
import os

import jwt
import requests


# -------------------------------------------------------------------
# Cube configuration
# -------------------------------------------------------------------

CUBE_API_URL = os.getenv(
    "CUBE_API_URL",
    "http://localhost:4000/cubejs-api/v1/load",
)

CUBE_API_SECRET = os.getenv(
    "CUBE_API_SECRET",
    "metricmind-local-development-secret-2026",
)


# -------------------------------------------------------------------
# Governed metric mapping
# -------------------------------------------------------------------

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


# -------------------------------------------------------------------
# Governed dimension mapping
# -------------------------------------------------------------------

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


# -------------------------------------------------------------------
# Time granularity mapping
# -------------------------------------------------------------------

GRANULARITY_MAP = {
    "Year": "year",
    "Quarter": "quarter",
    "Month": "month",
}


# -------------------------------------------------------------------
# Query limits
# -------------------------------------------------------------------

DEFAULT_RESULT_LIMIT = 10

# Time-series queries need more rows than categorical queries.
# 1000 is safely above the number of monthly/quarterly/yearly
# periods in the current Global Superstore dataset.
TIME_SERIES_LIMIT = 1000

REQUEST_TIMEOUT = 60


# -------------------------------------------------------------------
# Create Cube JWT
# -------------------------------------------------------------------

def _create_token():
    """
    Create a JWT token for local Cube API authentication.
    """
    return jwt.encode(
        {},
        CUBE_API_SECRET,
        algorithm="HS256",
    )


# -------------------------------------------------------------------
# Build Cube REST query
# -------------------------------------------------------------------

def _build_cube_query(structured_query):
    """
    Convert the governed AI-agent query into a Cube REST query.

    The AI agent never generates SQL.
    It only produces governed semantic concepts such as:

        Metric
        Dimension
        Time Granularity
        Filters
        Operation

    This function converts those concepts into Cube API syntax.
    """

    metric = structured_query.get("metric")
    dimension = structured_query.get("dimension")
    time_granularity = structured_query.get("time_granularity")
    operation = structured_query.get("operation")
    filters = structured_query.get("filters", {})

    if not isinstance(filters, dict):
        filters = {}

    # ---------------------------------------------------------------
    # Validate metric
    # ---------------------------------------------------------------

    if metric not in METRIC_MAP:
        raise ValueError(
            f"Unsupported metric: {metric}"
        )

    # ---------------------------------------------------------------
    # Validate dimension
    # ---------------------------------------------------------------

    if dimension is not None and dimension not in DIMENSION_MAP:
        raise ValueError(
            f"Unsupported dimension: {dimension}"
        )

    # ---------------------------------------------------------------
    # Validate time granularity
    # ---------------------------------------------------------------

    if (
        time_granularity is not None
        and time_granularity not in GRANULARITY_MAP
    ):
        raise ValueError(
            f"Unsupported time granularity: {time_granularity}"
        )

    measure = METRIC_MAP[metric]

    cube_dimension = (
        DIMENSION_MAP[dimension]
        if dimension is not None
        else None
    )

    # ---------------------------------------------------------------
    # Determine result limit
    # ---------------------------------------------------------------

    if time_granularity is not None:
        result_limit = TIME_SERIES_LIMIT
    else:
        result_limit = DEFAULT_RESULT_LIMIT

    # ---------------------------------------------------------------
    # Base Cube query
    # ---------------------------------------------------------------

    query = {
        "measures": [measure],
        "dimensions": (
            [cube_dimension]
            if cube_dimension is not None
            else []
        ),
        "limit": result_limit,
    }

    # ---------------------------------------------------------------
    # Time dimension
    #
    # Examples:
    #
    # Monthly:
    #   granularity = month
    #
    # Quarterly:
    #   granularity = quarter
    #
    # Yearly:
    #   granularity = year
    #
    # Year filter:
    #   dateRange = 2024-01-01 → 2024-12-31
    # ---------------------------------------------------------------

    if (
        time_granularity is not None
        or filters.get("Year") is not None
    ):

        time_dimension = {
            "dimension": "FactSales.orderDate",
        }

        # Add requested time granularity.
        if time_granularity is not None:
            time_dimension["granularity"] = (
                GRANULARITY_MAP[time_granularity]
            )

        # Add Year filter.
        if filters.get("Year") is not None:

            try:
                year = int(filters["Year"])
            except (TypeError, ValueError):
                raise ValueError(
                    "Year filter must be a valid integer."
                )

            if year < 1900 or year > 2100:
                raise ValueError(
                    f"Year filter is outside the supported range: {year}"
                )

            time_dimension["dateRange"] = [
                f"{year}-01-01",
                f"{year}-12-31",
            ]

        query["timeDimensions"] = [
            time_dimension
        ]

    # ---------------------------------------------------------------
    # Market filter
    #
    # Example:
    # "European sales"
    #
    # becomes:
    # Market = EU
    # ---------------------------------------------------------------

    if filters.get("Market") is not None:

        market = str(filters["Market"]).strip()

        if market:

            query["filters"] = [
                {
                    "member": "FactSales.market",
                    "operator": "equals",
                    "values": [market],
                }
            ]

    # ---------------------------------------------------------------
    # Ranking operations
    # ---------------------------------------------------------------

    if operation == "highest":

        query["order"] = {
            measure: "desc"
        }

        query["limit"] = 1

    elif operation == "lowest":

        query["order"] = {
            measure: "asc"
        }

        query["limit"] = 1

    # ---------------------------------------------------------------
    # Chronological ordering for time-series queries
    #
    # This ensures:
    #
    # Jan → Feb → Mar → ...
    #
    # instead of an arbitrary result order.
    # ---------------------------------------------------------------

    elif time_granularity is not None:

        query["order"] = {
            "FactSales.orderDate": "asc"
        }

    return query


# -------------------------------------------------------------------
# Execute Cube query
# -------------------------------------------------------------------

def execute_query(structured_query):
    """
    Execute a validated governed query against Cube.

    Returns the complete Cube API response.
    """

    cube_query = _build_cube_query(
        structured_query
    )

    token = _create_token()

    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
    }

    try:

        response = requests.get(
            CUBE_API_URL,
            params={
                "query": json.dumps(cube_query)
            },
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )

    except requests.exceptions.ConnectionError as exc:

        raise RuntimeError(
            "Could not connect to the Cube semantic API. "
            "Make sure Cube is running on localhost:4000."
        ) from exc

    except requests.exceptions.Timeout as exc:

        raise RuntimeError(
            "The Cube semantic API request timed out."
        ) from exc

    except requests.exceptions.RequestException as exc:

        raise RuntimeError(
            f"Cube API request failed: {exc}"
        ) from exc

    # ---------------------------------------------------------------
    # Handle Cube API errors with the actual response body.
    # This makes debugging much easier than a generic HTTP 400.
    # ---------------------------------------------------------------

    if not response.ok:

        try:
            error_body = response.json()
        except ValueError:
            error_body = response.text

        raise RuntimeError(
            "Cube API returned "
            f"HTTP {response.status_code}: "
            f"{error_body}"
        )

    # ---------------------------------------------------------------
    # Parse JSON response
    # ---------------------------------------------------------------

    try:

        return response.json()

    except ValueError as exc:

        raise RuntimeError(
            "Cube API returned an invalid JSON response."
        ) from exc


# -------------------------------------------------------------------
# Local test
# -------------------------------------------------------------------

if __name__ == "__main__":

    test_query = {
        "metric": "Sales",
        "dimension": None,
        "time_granularity": "Month",
        "filters": {
            "Year": 2024,
            "Market": None,
        },
        "operation": "total",
    }

    print("Testing Cube semantic client...", flush=True)

    try:

        cube_query = _build_cube_query(test_query)

        print("\nGenerated Cube query:", flush=True)
        print(
            json.dumps(
                cube_query,
                indent=2,
            ),
            flush=True,
        )

        result = execute_query(test_query)

        print(
            "\nCube query executed successfully.",
            flush=True,
        )

        print(
            f"Rows returned: {len(result.get('data', []))}",
            flush=True,
        )

        for row in result.get("data", [])[:5]:
            print(row, flush=True)

    except Exception as e:

        print(
            f"\nError: {e}",
            flush=True,
        )