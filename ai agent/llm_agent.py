from pathlib import Path
import re

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage


PROMPT_FILE = (
    Path(__file__).parent
    / "prompts"
    / "llm_system_prompt.txt"
)

system_prompt = PROMPT_FILE.read_text(
    encoding="utf-8"
)


llm = ChatOllama(
    model="llama3.1:latest",
    temperature=0,
)


def ask_llm(question: str) -> str:
    """
    Send a business question to Llama 3.1
    through LangChain.
    """

    response = llm.invoke(
        [
            SystemMessage(
                content=system_prompt
            ),
            HumanMessage(
                content=question
            ),
        ]
    )

    return response.content


def parse_llm_response(response: str):
    """
    Convert the governed LLM text response into
    a structured Python dictionary.

    Expected LLM format:

    Metric: Profit
    Dimension: Category
    Operation: highest
    Filter: Year = 2024

    The parser does not execute SQL and does not
    allow arbitrary query syntax.
    """

    if not isinstance(response, str):
        raise ValueError(
            "LLM response must be text."
        )

    fields = {}

    for line in response.splitlines():

        line = line.strip()

        if not line or ":" not in line:
            continue

        key, value = line.split(
            ":",
            1
        )

        key = key.strip().lower()
        value = value.strip()

        if key in {
            "metric",
            "dimension",
            "operation",
            "filter",
        }:
            fields[key] = value

    metric = fields.get("metric")
    dimension = fields.get("dimension")
    operation = fields.get("operation")
    filter_text = fields.get(
        "filter",
        ""
    )

    if not metric:
        raise ValueError(
            "LLM response did not contain a metric."
        )

    # ---------------------------------------------------------------
    # Parse dimension
    # ---------------------------------------------------------------

    if not dimension:
        dimension = None

    elif dimension.lower() in {
        "none",
        "null",
        "n/a",
    }:
        dimension = None

    # ---------------------------------------------------------------
    # Parse operation
    # ---------------------------------------------------------------

    if not operation:
        operation = None

    elif operation.lower() in {
        "none",
        "null",
        "n/a",
    }:
        operation = None

    # ---------------------------------------------------------------
    # Parse filters
    # ---------------------------------------------------------------

    filters = {
        "Year": None,
        "Market": None,
    }

    if filter_text:

        year_match = re.search(
            r"\b(?:year\s*=\s*)?(20\d{2})\b",
            filter_text,
            flags=re.IGNORECASE,
        )

        if year_match:
            filters["Year"] = int(
                year_match.group(1)
            )

        market_match = re.search(
            r"\bmarket\s*=\s*([A-Za-z_-]+)",
            filter_text,
            flags=re.IGNORECASE,
        )

        if market_match:
            filters["Market"] = (
                market_match.group(1)
                .strip()
                .upper()
            )

    return {
        "metric": metric,
        "dimension": dimension,
        "operation": operation,
        "filters": filters,
    }


def interpret_with_llm(question: str):
    """
    Run the complete LLM interpretation flow:

    Natural language
        ↓
    Llama 3.1
        ↓
    Governed text format
        ↓
    Structured Python dictionary
    """

    raw_response = ask_llm(
        question
    )

    parsed_response = parse_llm_response(
        raw_response
    )

    return {
        "raw_response": raw_response,
        "parsed_query": parsed_response,
    }


if __name__ == "__main__":

    question = (
        "Which category has the highest "
        "profit in 2024?"
    )

    print(
        "Sending question through LangChain...",
        flush=True,
    )

    try:

        result = interpret_with_llm(
            question
        )

        print(
            "\nLlama response:",
            flush=True,
        )

        print(
            result["raw_response"],
            flush=True,
        )

        print(
            "\nParsed query:",
            flush=True,
        )

        print(
            result["parsed_query"],
            flush=True,
        )

    except Exception as e:

        print(
            "\nError:",
            e,
            flush=True,
        )