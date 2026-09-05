from query_builder import build_query
from validator import validate_query


def process_question(question):
    """
    Process a user's natural-language question.

    Steps:
    1. Convert the question into a structured query.
    2. Check whether the query is ambiguous.
    3. Validate the structured query.
    4. Generate an appropriate response.
    """

    # Step 1: Build structured query
    structured_query = build_query(question)

    # Step 2: Validate the query
    validation_result = validate_query(structured_query)

    # Step 3: Check for ambiguity
    ambiguity = structured_query.get("ambiguity", {})

    if ambiguity.get("ambiguous", False):
        possible_metrics = ambiguity.get("possible_metrics", [])

        response = (
            "Your question is ambiguous. "
            "Please specify which metric you mean: "
            + ", ".join(possible_metrics)
            + "."
        )

    # Step 4: Handle invalid queries
    elif not validation_result["valid"]:
        errors = validation_result.get("errors", [])

        response = (
            "I could not process this question. "
            + " ".join(errors)
        )

    # Step 5: Valid query
    else:
        response = "Query is valid and ready for the semantic layer."

    return {
        "query": structured_query,
        "validation": validation_result,
        "response": response
    }