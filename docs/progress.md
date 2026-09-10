\# MetricMind Data \& Semantic Engineering Progress



\## Role



\*\*Data \& Semantic Engineer\*\*



The responsibility of this role is to prepare the analytical data layer,

implement the data warehouse models, validate data quality, and define the

governed business metrics required by the MetricMind semantic layer.



\---



\# 1. Project Data Pipeline



```text

Global Superstore CSV

&#x20;       ↓

Snowflake RAW

&#x20;       ↓

dbt STAGING

&#x20;       ↓

dbt INTERMEDIATE

&#x20;       ↓

dbt MART

&#x20;       ↓

Analytical Star Schema

&#x20;       ↓

Cube Semantic Layer

&#x20;       ↓

AI Agent

