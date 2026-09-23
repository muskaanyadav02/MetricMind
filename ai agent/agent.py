from query_builder import build_query
from validator import validate_query
from semantic_client import execute_query
from llm_agent import ask_llm, parse_llm_response


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
        [],
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


def _build_llm_query(question):
    """
    Ask Llama to interpret the business question and convert
    its governed response into the agent's internal schema.

    Deterministic query_builder logic is used to enrich
    the LLM result with time-series and root-cause information.
    """

    llm_response = ask_llm(question)

    parsed = parse_llm_response(
        llm_response
    )

    # Use the deterministic builder for information that the
    # current LLM prompt does not explicitly represent, such
    # as time granularity, root-cause intent and ambiguity.
    deterministic_query = build_query(
        question
    )

    # ---------------------------------------------------------------
    # Filters
    # ---------------------------------------------------------------

    filters = {
        "Year": parsed["filters"].get("Year"),
        "Market": parsed["filters"].get("Market"),
    }

    deterministic_filters = (
        deterministic_query.get(
            "filters",
            {}
        )
    )

    # Preserve deterministic filter detection if the LLM
    # does not explicitly provide the filter.
    if filters["Year"] is None:
        filters["Year"] = deterministic_filters.get(
            "Year"
        )

    if filters["Market"] is None:
        filters["Market"] = deterministic_filters.get(
            "Market"
        )

    # ---------------------------------------------------------------
    # Time-series information
    # ---------------------------------------------------------------

    time_granularity = deterministic_query.get(
        "time_granularity"
    )

    dimension = parsed.get(
        "dimension"
    )

    # The LLM may interpret words such as "time" as a dimension.
    # Time is handled through the governed time_granularity field,
    # not as a normal categorical dimension.
    if dimension is not None and dimension.lower() == "time":
        dimension = None

    # A time-series query should not keep Year as a
    # categorical dimension.
    if time_granularity is not None:
        if dimension == "Year":
            dimension = None

    # ---------------------------------------------------------------
    # Root-cause information
    # ---------------------------------------------------------------

    root_cause = deterministic_query.get(
        "root_cause",
        False,
    )

    root_cause_plan = deterministic_query.get(
        "root_cause_plan"
    )

    # ---------------------------------------------------------------
    # Metric
    # ---------------------------------------------------------------

    metric = parsed.get(
        "metric"
    )

    # ---------------------------------------------------------------
    # Operation
    # ---------------------------------------------------------------

    operation = parsed.get(
        "operation"
    )

    # Natural-language words such as "drop", "decline",
    # "fall" and "decrease" are root-cause intent indicators.
    # They are NOT governed query operations.
    #
    # For root-cause questions we first retrieve the primary
    # metric using a normal total query, then investigate
    # secondary governed metrics.
    if root_cause:
        operation = "total"

    # Time-series questions without an explicit operation
    # should retrieve the metric across the requested period.
    if (
        operation is None
        and time_granularity is not None
    ):
        operation = "total"

    # ---------------------------------------------------------------
    # Return final governed internal query
    # ---------------------------------------------------------------

    return {
        "question": question,
        "metric": metric,
        "dimension": dimension,
        "time_granularity": time_granularity,
        "filters": filters,
        "operation": operation,
        "root_cause": root_cause,
        "root_cause_plan": root_cause_plan,
        "ambiguity": deterministic_query.get(
            "ambiguity",
            {},
        ),
    }


def _interpret_question(question):
    """
    Interpret the question using Llama first.

    If the LLM is unavailable or produces an invalid
    governed response, fall back to the deterministic
    query builder.

    Every resulting query still passes through validation.
    """

    try:

        return _build_llm_query(
            question
        )

    except Exception as e:

        print(
            "LLM interpretation failed; "
            "using deterministic fallback: "
            f"{e}",
            flush=True,
        )

        return build_query(
            question
        )


def process_question(question):
    """
    Process a natural-language business question.

    Flow:

    1. Validate question input.
    2. Interpret question using Llama + LangChain.
    3. Fall back to deterministic interpretation if needed.
    4. Check ambiguity.
    5. Validate the governed structured query.
    6. Execute primary query through Cube.
    7. Detect empty results.
    8. Execute secondary queries for root-cause analysis.
    9. Return primary and secondary evidence.
    """

    # ---------------------------------------------------------------
    # Step 0: Validate question input
    # ---------------------------------------------------------------

    if not isinstance(
        question,
        str,
    ) or not question.strip():

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
    # Step 1: Interpret using Llama + LangChain
    # ---------------------------------------------------------------

    structured_query = _interpret_question(
        question
    )

    # ---------------------------------------------------------------
    # Step 2: Check ambiguity
    # ---------------------------------------------------------------

    ambiguity = structured_query.get(
        "ambiguity",
        {},
    )

    if ambiguity.get(
        "ambiguous",
        False,
    ):

        possible_metrics = ambiguity.get(
            "possible_metrics",
            [],
        )

        response = (
            "Your question is ambiguous. "
            "Please specify which metric you mean: "
            + ", ".join(
                possible_metrics
            )
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
    # Step 3: Validate the governed structured query
    # ---------------------------------------------------------------

    validation_result = validate_query(
        structured_query
    )

    if not validation_result["valid"]:

        errors = validation_result.get(
            "errors",
            [],
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
        [],
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
            if item.get(
                "semantic_result"
            ) is not None
            and item["semantic_result"].get(
                "data",
                [],
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