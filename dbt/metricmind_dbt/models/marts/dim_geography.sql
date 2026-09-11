SELECT DISTINCT
    CITY,
    STATE,
    COUNTRY,
    REGION,
    MARKET,
    MARKET2
FROM {{ ref('int_sales_enriched') }}
WHERE COUNTRY IS NOT NULL