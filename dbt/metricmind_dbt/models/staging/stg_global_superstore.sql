SELECT
    ROW_ID,
    ORDER_ID,
    ORDER_DATE,
    SHIP_DATE,

    CUSTOMER_ID,
    CUSTOMER_NAME,
    SEGMENT,

    PRODUCT_ID,
    PRODUCT_NAME,
    CATEGORY,
    SUB_CATEGORY,

    CITY,
    STATE,
    COUNTRY,
    REGION,
    MARKET,
    MARKET2,

    ORDER_PRIORITY,
    SHIP_MODE,

    QUANTITY,
    SALES,
    DISCOUNT,
    PROFIT,
    SHIPPING_COST,

    YEAR,
    WEEKNUM,
    RECORD_COUNT

FROM {{ source('metricmind_raw', 'raw_global_superstore') }}