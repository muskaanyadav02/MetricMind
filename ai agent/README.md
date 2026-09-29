# MetricMind — AI Agent

**An AI-powered conversational analytics agent for business intelligence.**

The MetricMind AI Agent enables users to explore business data using natural-language questions instead of writing queries manually. It interprets user intent, identifies relevant business metrics and dimensions, validates requests, and supports the process of transforming questions into structured analytical queries.

## Overview

Traditional business intelligence tools often require users to understand database schemas, metrics, and query syntax. MetricMind aims to make data exploration more accessible through a conversational interface.

The AI Agent serves as the intelligence layer between user questions and the analytics backend, helping users ask business questions in natural language and receive meaningful analytical results.

## Key Features

* **Natural-Language Query Interpretation:** Understands business questions and identifies the intended analytical operation.
* **Metric and Dimension Recognition:** Maps questions to supported business metrics and dimensions.
* **Query Building:** Converts interpreted requests into structured query specifications for the analytics workflow.
* **Semantic Validation:** Checks requests against the supported data model and helps identify unsupported or ambiguous questions.
* **Ambiguity Handling:** Identifies questions that need clarification when the intended metric or analytical meaning is unclear.
* **Backend Integration:** Works with the MetricMind backend to support the Ask AI experience.
* **Automated Testing:** Includes tests for agent interpretation and semantic-client behavior.

## How It Works

```text
User asks a business question
             |
             v
     AI Agent receives input
             |
             v
    Interpret user intent
             |
             v
 Identify metrics and dimensions
             |
             v
 Validate the request
             |
             v
 Build a structured query
             |
             v
  Analytics backend processes it
             |
             v
 Return results to Ask AI
```

The workflow helps connect conversational input with governed analytics while identifying requests that cannot be interpreted confidently.

## Example Questions

Users can explore supported business data with questions such as:

* Which category has the highest profit?
* What are the total sales by country?
* Show the quantity by region.
* Show the monthly sales trend.
* Compare sales across different years.

The questions that can be answered depend on the metrics, dimensions, operations, and time fields supported by the configured data model.

## Project Structure

```text
ai agent/
├── config/
│   └── config.py
├── prompts/
│   └── agent_prompt.txt
├── agent.py
├── llm_agent.py
├── query_builder.py
├── schema.py
├── validator.py
├── test_agent.py
├── test_semantic_client.py
├── requirements.txt
└── README.md
```

### Core Components

| Component                  | Responsibility                                    |
| -------------------------- | ------------------------------------------------- |
| `agent.py`                 | AI Agent workflow and orchestration               |
| `llm_agent.py`             | Language-model-related agent functionality        |
| `query_builder.py`         | Builds structured analytical query specifications |
| `schema.py`                | Defines schemas used by the agent                 |
| `validator.py`             | Validates interpreted requests                    |
| `config/config.py`         | Agent configuration                               |
| `prompts/agent_prompt.txt` | Instructions used by the agent                    |
| `test_agent.py`            | Tests agent interpretation and behavior           |
| `test_semantic_client.py`  | Tests related to semantic-client behavior         |
| `requirements.txt`         | Python dependencies                               |

## Technology Stack

* **Python** — Core agent logic and query processing.
* **Large Language Models (LLMs)** — Natural-language understanding and interpretation, where configured.
* **Semantic Validation** — Checks requests against supported analytics definitions.
* **FastAPI Backend** — Integration with MetricMind's backend services.
* **Pytest** — Automated testing.

## Validation and Reliability

MetricMind's AI Agent is designed to work with supported business metrics and dimensions rather than treating every natural-language request as a valid analytical query.

The validation workflow helps identify unsupported metrics and ambiguous questions before proceeding. This improves consistency between user intent and the analytical data available to the application.

## Running Tests

Run the tests from the root directory of the MetricMind repository:

```bash
python -m pytest "ai agent/test_agent.py" "ai agent/test_semantic_client.py" -v
```

To run the complete project test suite:

```bash
python -m pytest
```

## Integration with MetricMind

The AI Agent is part of the larger MetricMind analytics application. It works alongside the backend services and Ask AI frontend to support natural-language business analytics.

The complete application combines conversational interaction, governed analytical queries, backend processing, and the presentation of results.

## Future Enhancements

Potential future improvements include:

* Context-aware follow-up questions.
* More detailed explanations of analytical results.
* Automatic detection of unusual business trends.
* Interactive visualizations generated from query results.
* What-if analysis for business decision support.
* Improved clarification and error-recovery workflows.

## Project

**MetricMind — AI-Powered Business Analytics**

This module contributes to the project's goal of making business data more accessible through conversational analytics, structured query processing, and meaningful insights.
