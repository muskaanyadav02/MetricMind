from query_builder import build_query
from semantic_client import _build_cube_query


def test_revenue_by_category():
    structured_query = {
        "metric": "Revenue",
        "dimension": "Category",
        "operation": "total",
        "filters": {},
    }

    cube_query = _build_cube_query(
        structured_query
    )

    assert cube_query["measures"] == [
        "FactSales.revenue"
    ]

    assert cube_query["dimensions"] == [
        "FactSales.category"
    ]

    assert cube_query["limit"] == 10


def test_monthly_cube_query():
    structured_query = build_query(
        "Show the monthly sales trend"
    )

    cube_query = _build_cube_query(
        structured_query
    )

    assert cube_query["measures"] == [
        "FactSales.revenue"
    ]

    assert cube_query["dimensions"] == []

    assert cube_query["timeDimensions"] == [
        {
            "dimension": "FactSales.orderDate",
            "granularity": "month",
        }
    ]

    assert cube_query["limit"] == 1000

    assert cube_query["order"] == {
        "FactSales.orderDate": "asc"
    }


def test_quarterly_cube_query():
    structured_query = build_query(
        "Show the quarterly sales trend"
    )

    cube_query = _build_cube_query(
        structured_query
    )

    assert cube_query["timeDimensions"] == [
        {
            "dimension": "FactSales.orderDate",
            "granularity": "quarter",
        }
    ]

    assert cube_query["limit"] == 1000

    assert cube_query["order"] == {
        "FactSales.orderDate": "asc"
    }


def test_yearly_cube_query():
    structured_query = build_query(
        "Show the yearly sales trend"
    )

    cube_query = _build_cube_query(
        structured_query
    )

    assert cube_query["timeDimensions"] == [
        {
            "dimension": "FactSales.orderDate",
            "granularity": "year",
        }
    ]

    assert cube_query["limit"] == 1000

    assert cube_query["order"] == {
        "FactSales.orderDate": "asc"
    }


def test_monthly_cube_query_with_year_filter():
    structured_query = build_query(
        "Show monthly sales in 2014"
    )

    cube_query = _build_cube_query(
        structured_query
    )

    assert cube_query["timeDimensions"] == [
        {
            "dimension": "FactSales.orderDate",
            "granularity": "month",
            "dateRange": [
                "2014-01-01",
                "2014-12-31",
            ],
        }
    ]

    assert cube_query["limit"] == 1000

    assert cube_query["order"] == {
        "FactSales.orderDate": "asc"
    }


def test_monthly_european_sales_query():
    structured_query = build_query(
        "Show monthly sales in Europe"
    )

    cube_query = _build_cube_query(
        structured_query
    )

    assert cube_query["timeDimensions"] == [
        {
            "dimension": "FactSales.orderDate",
            "granularity": "month",
        }
    ]

    assert cube_query["filters"] == [
        {
            "member": "FactSales.market",
            "operator": "equals",
            "values": ["EU"],
        }
    ]

    assert cube_query["limit"] == 1000


def test_highest_profit_by_category():
    structured_query = {
        "metric": "Profit",
        "dimension": "Category",
        "operation": "highest",
        "filters": {},
    }

    cube_query = _build_cube_query(
        structured_query
    )

    assert cube_query["measures"] == [
        "FactSales.profit"
    ]

    assert cube_query["dimensions"] == [
        "FactSales.category"
    ]

    assert cube_query["order"] == {
        "FactSales.profit": "desc"
    }

    assert cube_query["limit"] == 1


def test_lowest_quantity_by_region():
    structured_query = {
        "metric": "Quantity Sold",
        "dimension": "Region",
        "operation": "lowest",
        "filters": {},
    }

    cube_query = _build_cube_query(
        structured_query
    )

    assert cube_query["measures"] == [
        "FactSales.quantitySold"
    ]

    assert cube_query["dimensions"] == [
        "FactSales.region"
    ]

    assert cube_query["order"] == {
        "FactSales.quantitySold": "asc"
    }

    assert cube_query["limit"] == 1