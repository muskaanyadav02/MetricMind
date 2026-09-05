from query_builder import build_query
from validator import validate_query


def process_question(question):
    """
    Process a user's natural-language question.

    Steps:
    1. Convert the question into a structured query.
    2. Validate the structured query.
    3. Return the query and validation result.
    """

    structured_query = build_query(question)
    validation_result = validate_query(structured_query)

    return {
        "query": structured_query,
        "validation": validation_result
    }