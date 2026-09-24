"""
MetricMind AI Agent

Responsibilities:
1. Interpret natural-language business questions.
2. Use Llama 3.1 through LangChain for semantic interpretation.
3. Normalize LLM output into MetricMind's governed schema.
4. Detect time-series questions deterministically.
5. Detect root-cause questions.
6. Validate the structured query.
7. Execute the governed query through the Cube semantic layer.
8. Handle no-data situations safely.
9. Perform secondary root-cause analysis when required.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from query_builder import (
    build_query,
    detect_root_cause_intent,
    build_root_cause_plan,
)
from validator import validate_query
from semantic_client import execute_query
from llm_agent import ask_llm, parse_llm_response


# ---------------------------------------------------------------------------
# LLM QUERY BUILDING
# ---------------------------------------------------------------------------

def _build_llm_query(question: str) -> Dict[str, Any]:
    """
    Use Llama 3.1 to interpret the question, then enrich and normalize
    the result using MetricMind's deterministic query builder.

    Important:
    LLM output is treated as an interpretation, not as the final
    governed query.

    This protects the semantic layer from unsupported LLM operations
    such as:
        Operation: trend
        Dimension: Month

    Time-series questions are represented internally as:

        time_granularity = Month / Quarter / Year
        dimension = None
        operation = total
    """

    # ---------------------------------------------------------------
    # 1. Ask Llama
    # ---------------------------------------------------------------

    raw_response = ask_llm(question)

    # ---------------------------------------------------------------
    # 2. Parse Llama's governed text response
    # ---------------------------------------------------------------

    parsed_response = parse_llm_response(raw_response)

    # ---------------------------------------------------------------
    # 3. Build deterministic interpretation
    # ---------------------------------------------------------------

    deterministic_query = build_query(question)

    # Start with the LLM interpretation.
    structured_query = {
        "question": question,
        "metric": parsed_response.get("metric"),
        "dimension": parsed_response.get("dimension"),
        "filters": parsed_response.get("filters", {}),
        "operation": parsed_response.get("operation"),
        "time_granularity": None,
        "root_cause": False,
        "root_cause_plan": None,
        "ambiguity": deterministic_query.get(
            "ambiguity",
            {},
        ),
    }

    # ---------------------------------------------------------------
    # 4. Preserve deterministic filters
    # ---------------------------------------------------------------

    deterministic_filters = deterministic_query.get(
        "filters",
        {},
    )

    if not isinstance(structured_query["filters"], dict):
        structured_query["filters"] = {}

    # Year
    if deterministic_filters.get("Year") is not None:
        structured_query["filters"]["Year"] = (
            deterministic_filters["Year"]
        )

    # Market
    if deterministic_filters.get("Market") is not None:
        structured_query["filters"]["Market"] = (
            deterministic_filters["Market"]
        )

    # ---------------------------------------------------------------
    # 5. Preserve deterministic ambiguity
    # ---------------------------------------------------------------

    structured_query["ambiguity"] = deterministic_query.get(
        "ambiguity",
        {},
    )

    # ---------------------------------------------------------------
    # 6. Detect time-series granularity deterministically
    # ---------------------------------------------------------------

    time_granularity = deterministic_query.get(
        "time_granularity"
    )

    if time_granularity is not None:

        structured_query["time_granularity"] = (
            time_granularity
        )

        # A time-series query must NOT use Month/Quarter/Year
        # as a normal categorical dimension.
        structured_query["dimension"] = None

        # Time-series queries are represented as total values
        # over chronological time buckets.
        #
        # "trend" is NOT a governed operation.
        structured_query["operation"] = "total"

    # ---------------------------------------------------------------
    # 7. Normalize LLM time-like dimensions
    # ---------------------------------------------------------------

    if structured_query.get("dimension") in {
        "Time",
        "time",
        "Date",
        "date",
        "Period",
        "period",
        "Month",
        "month",
        "Quarter",
        "quarter",
        "Year",
        "year",
    }:
        structured_query["dimension"] = None

    # ---------------------------------------------------------------
    # 8. Root-cause detection
    # ---------------------------------------------------------------

    root_cause = detect_root_cause_intent(question)

    if root_cause:

        structured_query["root_cause"] = True

        structured_query["root_cause_plan"] = (
            build_root_cause_plan(question)
        )

        # Root-cause analysis starts with the primary metric.
        # "trend" is not used as an operation.
        structured_query["operation"] = "total"

    # ---------------------------------------------------------------
    # 9. Final time-series safety normalization
    # ---------------------------------------------------------------

    # This is intentionally performed AFTER all LLM processing.
    #
    # Even if Llama returns:
    #
    # Metric: Sales
    # Dimension: Month
    # Operation: trend
    #
    # the final governed query becomes:
    #
    # Metric: Sales
    # Dimension: None
    # Time Granularity: Month
    # Operation: total

    if time_granularity is not None:

        structured_query["time_granularity"] = (
            time_granularity
        )

        structured_query["dimension"] = None

        structured_query["operation"] = "total"

    # ---------------------------------------------------------------
    # 10. Return normalized structured query
    # ---------------------------------------------------------------

    return structured_query


# ---------------------------------------------------------------------------
# NO-DATA RESPONSE
# ---------------------------------------------------------------------------

def _build_no_data_response(
    question: str,
    structured_query: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build a clear response when Cube returns no rows.
    """

    filters = structured_query.get(
        "filters",
        {},
    )

    metric = structured_query.get(
        "metric"
    )

    dimension = structured_query.get(
        "dimension"
    )

    time_granularity = structured_query.get(
        "time_granularity"
    )

    messages = []

    if filters.get("Year") is not None:
        messages.append(
            f"year {filters['Year']}"
        )

    if filters.get("Market") is not None:
        messages.append(
            f"market {filters['Market']}"
        )

    if time_granularity is not None:
        messages.append(
            f"{time_granularity.lower()} data"
        )

    if dimension is not None:
        messages.append(
            f"dimension '{dimension}'"
        )

    if messages:

        detail = ", ".join(messages)

        message = (
            f"No data was found for {metric} "
            f"with {detail}."
        )

    else:

        message = (
            f"No data was found for {metric} "
            f"for the requested question."
        )

    return {
        "status": "no_data",
        "answer": "",
        "message": message,
        "question": question,
        "query": structured_query,
        "data": [],
    }


# ---------------------------------------------------------------------------
# ROOT-CAUSE QUERY
# ---------------------------------------------------------------------------

def _build_root_cause_query(
    structured_query: Dict[str, Any],
    secondary_metric: str,
) -> Dict[str, Any]:
    """
    Build a governed secondary query for root-cause analysis.

    Currently the governed secondary cost driver is Shipping Cost.
    """

    return {
        "question": structured_query.get(
            "question",
            "",
        ),
        "metric": secondary_metric,
        "dimension": structured_query.get(
            "dimension"
        ),
        "time_granularity": structured_query.get(
            "time_granularity"
        ),
        "filters": structured_query.get(
            "filters",
            {},
        ),
        "operation": "total",
        "root_cause": False,
        "root_cause_plan": None,
        "ambiguity": {
            "ambiguous": False,
            "reason": None,
            "possible_metrics": [],
        },
    }


# ---------------------------------------------------------------------------
# ROOT-CAUSE EXECUTION
# ---------------------------------------------------------------------------

def _execute_root_cause_analysis(
    structured_query: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Execute secondary queries for root-cause analysis.

    Important:
    The agent reports supporting evidence.
    It does NOT claim that a secondary metric caused the primary
    metric change unless the evidence supports such a conclusion.
    """

    plan = structured_query.get(
        "root_cause_plan"
    )

    if not isinstance(plan, dict):
        return None

    if not plan.get("enabled"):
        return None

    secondary_metrics = plan.get(
        "secondary_metrics",
        [],
    )

    if not isinstance(
        secondary_metrics,
        list,
    ):
        return None

    evidence = []

    for secondary_metric in secondary_metrics:

        secondary_query = _build_root_cause_query(
            structured_query,
            secondary_metric,
        )

        validation = validate_query(
            secondary_query
        )

        if not validation.get("valid"):
            evidence.append(
                {
                    "metric": secondary_metric,
                    "status": "validation_failed",
                    "errors": validation.get(
                        "errors",
                        [],
                    ),
                }
            )
            continue

        try:

            result = execute_query(
                secondary_query
            )

            evidence.append(
                {
                    "metric": secondary_metric,
                    "status": "answered",
                    "result": result,
                }
            )

        except Exception as exc:

            evidence.append(
                {
                    "metric": secondary_metric,
                    "status": "execution_failed",
                    "message": str(exc),
                }
            )

    return {
        "enabled": True,
        "primary_metric": plan.get(
            "primary_metric"
        ),
        "secondary_metrics": secondary_metrics,
        "reason": plan.get(
            "reason"
        ),
        "evidence": evidence,
    }


# ---------------------------------------------------------------------------
# MAIN QUESTION PROCESSING
# ---------------------------------------------------------------------------

def process_question(
    question: str,
) -> Dict[str, Any]:
    """
    Complete AI-agent workflow:

        User question
              ↓
        Llama 3.1
              ↓
        LLM parser
              ↓
        Deterministic normalization
              ↓
        Validation
              ↓
        Cube semantic query
              ↓
        Snowflake
              ↓
        Optional root-cause analysis
    """

    # ---------------------------------------------------------------
    # 1. Validate input
    # ---------------------------------------------------------------

    if not isinstance(
        question,
        str,
    ):
        return {
            "status": "invalid",
            "answer": "",
            "message": (
                "Question must be a string."
            ),
            "data": [],
        }

    question = question.strip()

    if not question:
        return {
            "status": "invalid",
            "answer": "",
            "message": (
                "Question cannot be empty."
            ),
            "data": [],
        }

    # ---------------------------------------------------------------
    # 2. Interpret question with Llama
    # ---------------------------------------------------------------

    try:

        structured_query = _build_llm_query(
            question
        )

    except Exception as exc:

        return {
            "status": "error",
            "answer": "",
            "message": (
                "The AI agent could not "
                f"interpret the question: {exc}"
            ),
            "data": [],
        }

    # ---------------------------------------------------------------
    # 3. Check ambiguity
    # ---------------------------------------------------------------

    ambiguity = structured_query.get(
        "ambiguity",
        {},
    )

    if isinstance(
        ambiguity,
        dict,
    ) and ambiguity.get(
        "ambiguous"
    ):

        return {
            "status": "ambiguous",
            "answer": "",
            "message": ambiguity.get(
                "reason",
                "The question is ambiguous.",
            ),
            "ambiguity": ambiguity,
            "query": structured_query,
            "data": [],
        }

    # ---------------------------------------------------------------
    # 4. Validate governed query
    # ---------------------------------------------------------------

    validation = validate_query(
        structured_query
    )

    if not validation.get(
        "valid"
    ):

        return {
            "status": "unsupported",
            "answer": "",
            "message": (
                "The interpreted query "
                "is not supported."
            ),
            "validation": validation,
            "query": structured_query,
            "data": [],
        }

    # ---------------------------------------------------------------
    # 5. Execute primary semantic query
    # ---------------------------------------------------------------

    try:

        result = execute_query(
            structured_query
        )

    except Exception as exc:

        return {
            "status": "error",
            "answer": "",
            "message": (
                "The semantic query "
                f"could not be executed: {exc}"
            ),
            "query": structured_query,
            "data": [],
        }

    # ---------------------------------------------------------------
    # 6. Extract rows
    # ---------------------------------------------------------------

    rows = []

    if isinstance(
        result,
        dict,
    ):
        rows = result.get(
            "data",
            [],
        )

    elif isinstance(
        result,
        list,
    ):
        rows = result

    if rows is None:
        rows = []

    # ---------------------------------------------------------------
    # 7. Handle no data
    # ---------------------------------------------------------------

    if not rows:

        response = _build_no_data_response(
            question,
            structured_query,
        )

        response["validation"] = validation
        response["semantic_result"] = result

        return response

    # ---------------------------------------------------------------
    # 8. Root-cause analysis
    # ---------------------------------------------------------------

    root_cause_analysis = None

    if structured_query.get(
        "root_cause"
    ):

        root_cause_analysis = (
            _execute_root_cause_analysis(
                structured_query
            )
        )

    # ---------------------------------------------------------------
    # 9. Build deterministic answer
    # ---------------------------------------------------------------

    metric = structured_query.get(
        "metric"
    )

    dimension = structured_query.get(
        "dimension"
    )

    operation = structured_query.get(
        "operation"
    )

    time_granularity = structured_query.get(
        "time_granularity"
    )

    # Time-series questions return the complete series.
    if time_granularity is not None:

        answer = (
            f"{metric} trend by "
            f"{time_granularity.lower()} "
            f"returned {len(rows)} data points."
        )

    # Highest
    elif operation == "highest":

        answer = (
            f"Highest {metric} by "
            f"{dimension} returned."
        )

    # Lowest
    elif operation == "lowest":

        answer = (
            f"Lowest {metric} by "
            f"{dimension} returned."
        )

    # Compare
    elif operation == "compare":

        answer = (
            f"{metric} comparison by "
            f"{dimension} returned."
        )

    # Normal total
    else:

        if dimension is not None:

            answer = (
                f"{metric} by "
                f"{dimension} returned "
                f"{len(rows)} result(s)."
            )

        else:

            answer = (
                f"{metric} returned "
                f"{len(rows)} result(s)."
            )

    # ---------------------------------------------------------------
    # 10. Return final response
    # ---------------------------------------------------------------

    return {
        "status": "answered",
        "answer": answer,
        "message": "",
        "ambiguity": ambiguity,
        "query": structured_query,
        "validation": validation,
        "semantic_result": result,
        "root_cause_analysis": root_cause_analysis,
        "data": rows,
    }


# ---------------------------------------------------------------------------
# BACKEND ADAPTER ENTRY POINT
# ---------------------------------------------------------------------------

def interpret(
    question: str,
) -> Dict[str, Any]:
    """
    Public interpretation entry point used by the backend adapter.

    Unlike process_question(), this function only interprets the
    question and does not execute Cube.
    """

    if not isinstance(
        question,
        str,
    ) or not question.strip():

        raise ValueError(
            "A non-empty question is required."
        )

    return _build_llm_query(
        question.strip()
    )


# ---------------------------------------------------------------------------
# MANUAL TESTING
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    questions = [
        "Which category has the highest profit in 2014?",
        "Show the monthly sales trend",
        "Show the quarterly sales trend",
        "Show the yearly sales trend",
        "Show monthly sales in 2014",
        "Show monthly sales in Europe",
        "Why did profit margin drop?",
    ]

    for question in questions:

        print("\n" + "=" * 70)
        print(
            f"Question: {question}"
        )
        print("=" * 70)

        try:

            interpreted = _build_llm_query(
                question
            )

            print(
                "\nStructured query:"
            )

            print(
                interpreted
            )

        except Exception as exc:

            print(
                f"\nError: {exc}"
            )