# MetricMind Development Progress

## Day 1 — Project Initialization

### Completed
- Reviewed the MetricMind architecture.
- Confirmed Data & Semantic Engineering responsibilities.
- Created the initial data engineering folder structure.
- Established documentation structure.
- Identified the initial technology stack.
- Defined initial business metrics.

### Technology
- Python
- SQL
- Snowflake
- dbt
- Cube.dev
- YAML
- Git/GitHub

### Next Steps
- Design the enterprise dataset.
- Define tables, columns, keys, relationships, and data grain.
- Generate synthetic enterprise data.

### Status
🟢 Foundation established.


## Day 2 — Source Dataset Analysis

### Completed

- Inspected the existing 50,000-row Global Superstore dataset.
- Identified major business entities including customers, products,
  orders, sales, geography, and shipping.
- Confirmed that the raw source dataset should remain unchanged.
- Created an initial data validation script using Python and Pandas.
- Started profiling row counts, unique identifiers, missing values,
  duplicates, numerical fields, and date fields.
- Defined the initial business metrics required by MetricMind.

## Day 3 — Snowflake RAW Layer

- Created the METRICMIND database.
- Created the RAW schema.
- Created the METRICMIND_WH X-Small warehouse.
- Configured auto-suspend and auto-resume.
- Created the RAW_GLOBAL_SUPERSTORE table.
- Prepared the Snowflake RAW layer for Global Superstore ingestion.
- Next: Load and validate the source CSV.

## Day 3 — Snowflake RAW Layer

- Created METRICMIND database.
- Created RAW schema.
- Created METRICMIND_WH warehouse.
- Created RAW_GLOBAL_SUPERSTORE table.
- Loaded Global Superstore source data.
- Validated row count and key business entities.
- Confirmed RAW layer is ready for dbt transformation.

### Validation

- Total rows: 51,290
- Unique orders: 25,035
- Unique customers: 4,873
- Unique products: 10,292

### Next

- Initialize dbt project.
- Connect dbt to Snowflake.
- Create staging models.

### Initial Metrics

- Revenue
- Profit
- Profit Margin
- Orders
- Customers
- Quantity Sold
- Average Order Value
- Shipping Cost

### Next Steps

- Complete data-quality profiling.
- Finalize the data dictionary.
- Design the Snowflake RAW layer.
- Load the raw dataset into Snowflake.

### Status

🟢 Dataset analysis in progress.

## Day 2 — Dataset Profiling & Data Modeling

### Completed

- Profiled the source Global Superstore dataset using Python and Pandas.
- Confirmed 51,290 transaction records across 27 columns.
- Identified 25,035 unique orders, 10,292 products, and 4,873 customers.
- Confirmed zero duplicate rows and zero missing values.
- Identified the dataset grain as order-line-level transactions.
- Verified that multiple rows can belong to the same order.
- Identified `Market = EU` as the geographic representation of the European market.
- Defined initial governed business metrics.
- Identified the required fact and dimension model.

### Initial Business Metrics

- Revenue
- Profit
- Profit Margin
- Orders
- Customers
- Quantity Sold
- Shipping Cost
- Average Order Value

### Data Modeling

Initial analytical model:

- fact_sales
- dim_customer
- dim_product
- dim_geography
- dim_date

### Next Steps

- Configure Snowflake.
- Create the RAW database/schema.
- Load the source dataset into Snowflake.
- Validate row counts and source data integrity.

### Status

🟢 Dataset profiling completed.
🟢 Initial data model defined.