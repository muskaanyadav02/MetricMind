from query_builder import build_query
from validator import validate_query
from llm_agent import ask_llm, parse_llm_response


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
    Run real end-to-end LLM + agent + Cube tests.

    This function is intentionally manual so that pytest
    does not repeatedly invoke the local Llama model.
    """

    from agent import process_question

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
# Fast deterministic query tests
# -------------------------------------------------------------------

def test_monthly_sales_trend():

    query = build_query(
        "Show the monthly sales trend"
    )

    validation = validate_query(query)

    assert validation["valid"] is True

    assert query["metric"] == "Sales"

    assert query["time_granularity"] == "Month"

    assert query["operation"] == "total"


def test_monthly_sales_with_year_filter():

    query = build_query(
        "Show monthly sales in 2014"
    )

    validation = validate_query(query)

    assert validation["valid"] is True

    assert query["metric"] == "Sales"

    assert query["time_granularity"] == "Month"

    assert query["filters"]["Year"] == 2014


def test_quarterly_sales_trend():

    query = build_query(
        "Show the quarterly sales trend"
    )

    validation = validate_query(query)

    assert validation["valid"] is True

    assert query["metric"] == "Sales"

    assert query["time_granularity"] == "Quarter"

    assert query["operation"] == "total"


def test_yearly_sales_trend():

    query = build_query(
        "Show the yearly sales trend"
    )

    validation = validate_query(query)

    assert validation["valid"] is True

    assert query["metric"] == "Sales"

    assert query["time_granularity"] == "Year"

    assert query["operation"] == "total"


# -------------------------------------------------------------------
# Fast query-builder no-data test
# -------------------------------------------------------------------

def test_no_data_for_unavailable_year():

    query = build_query(
        "Show monthly sales in 2024"
    )

    validation = validate_query(query)

    assert validation["valid"] is True

    assert query["filters"]["Year"] == 2024

    assert query["time_granularity"] == "Month"


# -------------------------------------------------------------------
# LLM integration test
# -------------------------------------------------------------------

def test_llm_parser():

    response = ask_llm(
        "Which category has the highest profit in 2024?"
    )

    parsed = parse_llm_response(response)

    assert parsed["metric"] == "Profit"

    assert parsed["dimension"] == "Category"

    assert parsed["operation"] == "highest"

    assert parsed["filters"]["Year"] == 2024


# -------------------------------------------------------------------
# Run manual tests only when this file is executed directly
# -------------------------------------------------------------------

if __name__ == "__main__":
    run_manual_tests()