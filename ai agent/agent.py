from query_builder import build_query
from validator import validate_query


def process_question(question):
    """
    Process a natural-language business question.

    Flow:
    1. Build a structured semantic query.
    2. Check ambiguity.
    3. Validate the structured query.
    4. Return the validated agent output.
    """

    if not isinstance(question, str) or not question.strip():
        return {
            "query": {},
            "validation": {
                "valid": False,
                "errors": ["Question cannot be empty."]
            },
            "response": "Please provide a business question."
        }

    # Step 1: Build structured query
    structured_query = build_query(question)

    # Step 2: Check ambiguity
    ambiguity = structured_query.get("ambiguity", {})

    if ambiguity.get("ambiguous", False):
        possible_metrics = ambiguity.get("possible_metrics", [])

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
                "errors": ["Question is ambiguous."]
            },
            "response": response
        }

    # Step 3: Validate structured query
    validation_result = validate_query(structured_query)

    if not validation_result["valid"]:
        errors = validation_result.get("errors", [])

        response = (
            "I could not process this question. "
            + " ".join(errors)
        )

        return {
            "query": structured_query,
            "validation": validation_result,
            "response": response
        }

    return {
        "query": structured_query,
        "validation": validation_result,
        "response": (
            "Query is valid and ready for the governed semantic layer."
        )
    }