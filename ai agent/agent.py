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


def _build_root_cause_query(
    primary_query,
    secondary_metric,
):
    """
    Build a governed secondary query for root-cause analysis.

    The secondary query reuses the original filters and
    time granularity but changes only the metric.

    No SQL or unrestricted query syntax is generated.
    """

    return {
        "question": (
            "Secondary root-cause analysis for "
            f"{primary_query.get('question', '')}"
        ),
        "metric": secondary_metric,
        "dimension": primary_query.get("dimension"),
        "time_granularity": primary_query.get(
            "time_granularity"
        ),
        "filters": dict(
            primary_query.get("filters", {})
        ),
        "operation": (
            primary_query.get("operation")
            or "total"
        ),
        "root_cause": False,
        "root_cause_plan": None,
        "ambiguity": {
            "ambiguous": False,
            "reason": None,
            "possible_metrics": [],
        },
    }


def _execute_root_cause_analysis(
    primary_query,
):
    """
    Execute the governed secondary queries required for
    root-cause analysis.

    Currently the semantic layer provides Shipping Cost
    as the available secondary cost driver.

    The result is returned as evidence. It does not claim
    that the secondary metric caused the primary change.
    """

    root_cause_plan = primary_query.get(
        "root_cause_plan"
    )

    if not root_cause_plan:
        return None

    secondary_metrics = root_cause_plan.get(
        "secondary_metrics",
        []
    )

    analysis = []

    for secondary_metric in secondary_metrics:

        secondary_query = _build_root_cause_query(
            primary_query,
            secondary_metric,
        )

        secondary_validation = validate_query(
            secondary_query
        )

        if not secondary_validation["valid"]:
            analysis.append(
                {
                    "metric": secondary_metric,
                    "query": secondary_query,
                    "validation": secondary_validation,
                    "semantic_result": None,
                    "error": (
                        "Secondary query failed validation."
                    ),
                }
            )
            continue

        try:
            secondary_result = execute_query(
                secondary_query
            )

            analysis.append(
                {
                    "metric": secondary_metric,
                    "query": secondary_query,
                    "validation": secondary_validation,
                    "semantic_result": secondary_result,
                    "error": None,
                }
            )

        except Exception as e:
            analysis.append(
                {
                    "metric": secondary_metric,
                    "query": secondary_query,
                    "validation": secondary_validation,
                    "semantic_result": None,
                    "error": str(e),
                }
            )

    return analysis


def process_question(question):
    """
    Process a natural-language business question.

    Flow:
    1. Build a structured semantic query.
    2. Check ambiguity.
    3. Validate the structured query.
    4. Execute the validated query through Cube.
    5. Detect empty results.
    6. If root-cause intent exists, execute governed
       secondary queries.
    7. Return the primary result and root-cause evidence.
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
    # Step 4: Execute primary query through Cube
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
    # Step 5: Check for empty primary result
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
            "root_cause_analysis": None,
        }

    # ---------------------------------------------------------------
    # Step 6: Execute multi-step root-cause analysis
    # ---------------------------------------------------------------

    root_cause_analysis = None

    if structured_query.get(
        "root_cause",
        False,
    ):

        root_cause_analysis = (
            _execute_root_cause_analysis(
                structured_query
            )
        )

    # ---------------------------------------------------------------
    # Step 7: Build response
    # ---------------------------------------------------------------

    if root_cause_analysis:

        successful_secondary_queries = [
            item
            for item in root_cause_analysis
            if item.get("semantic_result") is not None
            and item["semantic_result"].get(
                "data",
                []
            )
        ]

        if successful_secondary_queries:

            response = (
                "Primary metric analyzed successfully "
                "through the governed semantic layer. "
                "I also queried the available secondary "
                "cost drivers for root-cause evidence."
            )

        else:

            response = (
                "Primary metric analyzed successfully "
                "through the governed semantic layer. "
                "No secondary cost-driver data was available."
            )

    else:

        response = (
            "Query executed successfully "
            "through the governed semantic layer."
        )

    # ---------------------------------------------------------------
    # Step 8: Return complete result
    # ---------------------------------------------------------------

    return {
        "query": structured_query,
        "validation": validation_result,
        "response": response,
        "semantic_result": semantic_result,
        "root_cause_analysis": root_cause_analysis,
    }