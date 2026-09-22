from agent import process_question


# -------------------------------------------------------------------
# Manual end-to-end test questions
# -------------------------------------------------------------------

questions = [
    "Which category made the most profit?",
    "Show sales by country",
    "Compare quantity by region",
    "Which category had the highest profit in 2014?",
    "Show total sales by country in 2014",
    "What region had the lowest quantity?",
    "What is the average sales by market?",
    "Show customer happiness by country",
    "Show me the best products",
    "Which is the best category?",
    "Show me the best products by profit",
    "Show me European sales",
]


def run_manual_tests():
    """
    Run real end-to-end agent + Cube tests.
    """

    for question in questions:

        result = process_question(question)

        print("\nQuestion:", question)
        print(
            "Structured Query:",
            result["query"]
        )
        print(
            "Validation:",
            result["validation"]
        )
        print(
            "Agent Response:",
            result["response"]
        )

        if "semantic_result" in result:
            print(
                "Semantic Result:",
                result["semantic_result"]
            )


# -------------------------------------------------------------------
# Automated time-series tests
# -------------------------------------------------------------------

def test_monthly_sales_trend():

    result = process_question(
        "Show the monthly sales trend"
    )

    query = result["query"]

    assert result["validation"]["valid"] is True

    assert query["metric"] == "Sales"

    assert query["time_granularity"] == "Month"

    assert query["operation"] == "total"


def test_monthly_sales_with_year_filter():

    result = process_question(
        "Show monthly sales in 2014"
    )

    query = result["query"]

    assert result["validation"]["valid"] is True

    assert query["metric"] == "Sales"

    assert query["time_granularity"] == "Month"

    assert query["filters"]["Year"] == 2014


def test_quarterly_sales_trend():

    result = process_question(
        "Show the quarterly sales trend"
    )

    query = result["query"]

    assert result["validation"]["valid"] is True

    assert query["metric"] == "Sales"

    assert query["time_granularity"] == "Quarter"

    assert query["operation"] == "total"


def test_yearly_sales_trend():

    result = process_question(
        "Show the yearly sales trend"
    )

    query = result["query"]

    assert result["validation"]["valid"] is True

    assert query["metric"] == "Sales"

    assert query["time_granularity"] == "Year"

    assert query["operation"] == "total"


# -------------------------------------------------------------------
# Run manual tests only when this file is executed directly
# -------------------------------------------------------------------

if __name__ == "__main__":
    run_manual_tests()