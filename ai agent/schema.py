# Governed business metrics available to the AI agent.
#
# These names are accepted by the backend's agent adapter and are
# translated to the governed semantic-layer metrics.

METRICS = [
    "Sales",
    "Revenue",
    "Profit",
    "Profit Margin",
    "Orders",
    "Customers",
    "Quantity",
    "Quantity Sold",
    "Shipping Cost",
    "Average Order Value",
]


# Approved business dimensions.
#
# These are categorical dimensions that can be used to group
# business metrics.

DIMENSIONS = [
    "Year",
    "Country",
    "Market",
    "Region",
    "Category",
    "Sub-Category",
    "Product Name",
    "Ship Mode",
    "Order Priority",
]


# Approved time granularities.
#
# These are intentionally kept separate from DIMENSIONS because
# Cube handles time grouping through a time dimension plus a
# granularity such as month, quarter, or year.

TIME_GRANULARITIES = [
    "Year",
    "Quarter",
    "Month",
]