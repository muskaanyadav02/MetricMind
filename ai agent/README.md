# AI Agent

The AI Agent is responsible for understanding natural-language business questions and converting them into structured semantic queries for the MetricMind governed semantic layer.

## Responsibilities

- Identify business metrics from user questions.
- Identify business dimensions.
- Detect year-based filters.
- Identify supported operations such as total, highest, lowest, and compare.
- Detect ambiguous questions.
- Validate structured agent queries.
- Prevent unsupported metrics and operations from being passed forward.
- Produce structured output instead of raw SQL.

## Technologies

- Python
- LangChain
- Llama 3
- Cube.dev API

## Agent Workflow

User Question
→ Intent and Metric Identification
→ Structured Semantic Query
→ Query Validation
→ Governed Semantic Layer
→ Query Result
→ Business Response

## Structured Query Format

The agent produces structured output containing:

- Question
- Metric
- Dimension
- Filters
- Operation
- Ambiguity information

Example:

```text
Question:
"Show revenue by country in 2024"

Structured Query:
Metric: Revenue
Dimension: Country
Filter: Year = 2024
Operation: None