WITH ranked_products AS (

    SELECT
        PRODUCT_ID,
        PRODUCT_NAME,
        CATEGORY,
        SUB_CATEGORY,

        ROW_NUMBER() OVER (
            PARTITION BY PRODUCT_ID
            ORDER BY PRODUCT_NAME, CATEGORY, SUB_CATEGORY
        ) AS RN

    FROM {{ ref('int_sales_enriched') }}

    WHERE PRODUCT_ID IS NOT NULL
)

SELECT
    PRODUCT_ID,
    PRODUCT_NAME,
    CATEGORY,
    SUB_CATEGORY

FROM ranked_products

WHERE RN = 1