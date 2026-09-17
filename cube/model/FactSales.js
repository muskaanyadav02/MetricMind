cube(`FactSales`, {
  sql_table: `METRICMIND.MART.FACT_SALES`,

  measures: {
    revenue: {
      type: `sum`,
      sql: `SALES`
    },

    profit: {
      type: `sum`,
      sql: `PROFIT`
    },

    quantitySold: {
      type: `sum`,
      sql: `QUANTITY`
    },

    shippingCost: {
      type: `sum`,
      sql: `SHIPPING_COST`
    },

    orders: {
      type: `countDistinct`,
      sql: `ORDER_ID`
    },

    customers: {
      type: `countDistinct`,
      sql: `CUSTOMER_ID`
    },

    profitMargin: {
      type: `number`,
      sql: `100.0 * ${profit} / NULLIF(${revenue}, 0)`
    },

    averageOrderValue: {
      type: `number`,
      sql: `${revenue} / NULLIF(${orders}, 0)`
    }
  },

  dimensions: {
    rowId: {
      sql: `ROW_ID`,
      type: `number`,
      primaryKey: true
    },

    orderId: {
      sql: `ORDER_ID`,
      type: `string`
    },

    orderDate: {
      sql: `ORDER_DATE`,
      type: `time`
    },

    customerId: {
      sql: `CUSTOMER_ID`,
      type: `string`
    },

    customerName: {
      sql: `CUSTOMER_NAME`,
      type: `string`
    },

    productId: {
      sql: `PRODUCT_ID`,
      type: `string`
    },

    productName: {
      sql: `PRODUCT_NAME`,
      type: `string`
    },

    category: {
      sql: `CATEGORY`,
      type: `string`
    },

    subCategory: {
      sql: `SUB_CATEGORY`,
      type: `string`
    },

    segment: {
      sql: `SEGMENT`,
      type: `string`
    },

    city: {
      sql: `CITY`,
      type: `string`
    },

    state: {
      sql: `STATE`,
      type: `string`
    },

    country: {
      sql: `COUNTRY`,
      type: `string`
    },

    region: {
      sql: `REGION`,
      type: `string`
    },

    market: {
      sql: `MARKET`,
      type: `string`
    },

    market2: {
      sql: `MARKET2`,
      type: `string`
    },

    shipMode: {
      sql: `SHIP_MODE`,
      type: `string`
    },

    orderPriority: {
      sql: `ORDER_PRIORITY`,
      type: `string`
    }
  }
});