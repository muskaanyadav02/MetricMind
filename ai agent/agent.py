from query_builder import build_query
from validator import validate_query
from semantic_client import execute_query


def process_question(question):
    """
    Process a user's natural-language question.

    Flow:
    1. Convert the question into a structured query.
    2. Check for ambiguity.
    3. Validate the structured query.
    4. If valid, send it to the semantic layer client.
    """

    # Step 1: Build structured query
    structured_query = build_query(question)

    # Step 2: Check ambiguity
    ambiguity = structured_query.get("ambiguity", {})

    if ambiguity.get("ambiguous", False):
        possible_metrics = ambiguity.get("possible_metrics", [])

        if possible_metrics:
            response = (
                "Your question is ambiguous. "
                "Please specify which metric you mean: "
                + ", ".join(possible_metrics)
                + "."
            )
        else:
            response = (
                "Your question is ambiguous. "
                "Please provide more details."
            )

        return {
            "query": structured_query,
            "validation": {
                "valid": False,
                "errors": ["Question is ambiguous."]
            },
            "response": response
        }

    # Step 3: Validate query
    validation_result = validate_query(structured_query)

    if not validation_result["valid"]:
        errors = validation_result.get("errors", [])

        if errors:
            response = "I could not process this question. " + " ".join(errors)
        else:
            response = "I could not process this question."

        return {
            "query": structured_query,
            "validation": validation_result,
            "response": response
        }

    # Step 4: Send valid query to semantic layer
    semantic_result = execute_query(structured_query)

    return {
        "query": structured_query,
        "validation": validation_result,
        "semantic_result": semantic_result,
        "response": "Query is valid and ready for the semantic layer."
    }