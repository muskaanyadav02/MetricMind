from query_builder import build_query
from validator import validate_query
from semantic_client import execute_query


def _build_no_data_response(structured_query):
    """
    Build a clear response when the semantic query succeeds
    but returns no data.
    """

    filters = structured_query.get("filters", {})

    year = filters.get("Year")

    if year is not None:
        return (
            f"No data was found for {year}. "
            "The available dataset covers the years 2011 to 2014."
        )

    market = filters.get("Market")

    if market is not None:
        return (
            f"No data was found for the requested market: {market}."
        )

    time_granularity = structured_query.get(
        "time_granularity"
    )

    if time_granularity is not None:
        return (
            "No data was found for the requested time period."
        )

    dimension = structured_query.get("dimension")

    if dimension is not None:
        return (
            "No data was found for the requested "
            f"{dimension.lower()}."
        )

    return "No data was found for this query."


def process_question(question):
    """
    Process a natural-language business question.

    Flow:
    1. Build a structured semantic query.
    2. Check ambiguity.
    3. Validate the structured query.
    4. Execute the validated query through Cube.
    5. Detect empty results.
    6. Return the semantic result.
    """

    # ---------------------------------------------------------------
    # Step 0: Validate question input
    # ---------------------------------------------------------------

    if not isinstance(question, str) or not question.strip():

        return {
            "query": {},
            "validation": {
                "valid": False,
                "errors": [
                    "Question cannot be empty."
                ],
            },
            "response": (
                "Please provide a business question."
            ),
        }

    # ---------------------------------------------------------------
    # Step 1: Build structured semantic query
    # ---------------------------------------------------------------

    structured_query = build_query(question)

    # ---------------------------------------------------------------
    # Step 2: Check ambiguity
    # ---------------------------------------------------------------

    ambiguity = structured_query.get(
        "ambiguity",
        {}
    )

    if ambiguity.get("ambiguous", False):

        possible_metrics = ambiguity.get(
            "possible_metrics",
            []
        )

        response = (
            "Your question is ambiguous. "
            "Please specify which metric you mean: "
            + ", ".join(possible_metrics)
            + "."
        )

        return {
            "query": structured_query,
            "validation": {
                "valid": False,
                "errors": [
                    "Question is ambiguous."
                ],
            },
            "response": response,
        }

    # ---------------------------------------------------------------
    # Step 3: Validate structured query
    # ---------------------------------------------------------------

    validation_result = validate_query(
        structured_query
    )

    if not validation_result["valid"]:

        errors = validation_result.get(
            "errors",
            []
        )

        response = (
            "I could not process this question. "
            + " ".join(errors)
        )

        return {
            "query": structured_query,
            "validation": validation_result,
            "response": response,
        }

    # ---------------------------------------------------------------
    # Step 4: Execute through Cube semantic layer
    # ---------------------------------------------------------------

    try:

        semantic_result = execute_query(
            structured_query
        )

    except Exception as e:

        return {
            "query": structured_query,
            "validation": validation_result,
            "response": (
                f"Query execution failed: {e}"
            ),
            "semantic_result": None,
        }

    # ---------------------------------------------------------------
    # Step 5: Check for empty result
    # ---------------------------------------------------------------

    data = semantic_result.get(
        "data",
        []
    )

    if not data:

        return {
            "query": structured_query,
            "validation": validation_result,
            "response": _build_no_data_response(
                structured_query
            ),
            "semantic_result": semantic_result,
        }

    # ---------------------------------------------------------------
    # Step 6: Return successful semantic result
    # ---------------------------------------------------------------

    return {
        "query": structured_query,
        "validation": validation_result,
        "response": (
            "Query executed successfully "
            "through the governed semantic layer."
        ),
        "semantic_result": semantic_result,
    }