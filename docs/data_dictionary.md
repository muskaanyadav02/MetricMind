# Data Dictionary

## Core Entities

MetricMind will use the following enterprise datasets:

- Customers
- Products
- Orders
- Order Items
- Returns
- Costs
- Regions

Detailed column definitions, data types, keys, relationships, and grain
will be documented during the data modeling phase.

# MetricMind Data Dictionary

## Source Dataset

File: `global_superstore_raw.csv`

Approximate Records: 50,000

The source dataset is maintained as raw data and will not be
modified directly. Data cleaning and transformation will be
performed downstream using dbt.

## Data Grain

The dataset represents order-line-level sales transactions.
Each row represents a product associated with an order.

## Core Entities

### Customer

Identified by `Customer.ID`.

### Product

Identified by `Product.ID`.

### Order

Identified by `Order.ID`.

### Geography

Represented by country, state, city, region, and market.

### Sales Transaction

Contains quantity, sales, discount, profit, and shipping cost.