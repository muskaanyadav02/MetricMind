# MetricMind Architecture

## Data & Semantic Engineering Architecture

The Data & Semantic Engineering pipeline follows:

Raw Dataset
→ Snowflake
→ dbt
→ Analytical Data Models
→ Cube.dev Semantic Layer
→ Governed Semantic API
→ AI Agent

## Core Technologies

- Python
- SQL
- Snowflake
- dbt
- Cube.dev
- YAML
- Git/GitHub

## Responsibility

The Data & Semantic Engineering layer is responsible for:

- Dataset preparation
- Data warehousing
- Data transformation
- Data modeling
- Data quality
- Business metric definitions
- Semantic layer implementation
- Semantic API validation

# MetricMind Data & Semantic Engineering Architecture

## Current Data Flow

Raw CSV
↓
Snowflake RAW
↓
dbt Staging
↓
dbt Intermediate Models
↓
dbt Analytical Marts
↓
Cube.dev Semantic Layer
↓
Cube Semantic API
↓
AI Agent

## Source Dataset

The initial source dataset is the Global Superstore dataset
containing approximately 50,000 records.

## Data Engineering Principle

The original source data will be preserved as raw data.

Data cleaning, transformation, modeling, testing, and business
logic will be implemented downstream using dbt.

## Semantic Engineering

Cube.dev will expose governed business metrics and dimensions
to downstream applications and AI agents.

The AI agent will consume governed semantic definitions rather
than directly querying raw warehouse tables.
