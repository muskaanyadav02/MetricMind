import React from "react";
import ReactECharts from "echarts-for-react";


/* =========================================================
   NUMBER FORMATTER
   ========================================================= */

function formatNumber(value) {
  const number = Number(value);

  if (!Number.isFinite(number)) {
    return "0";
  }

  const absolute = Math.abs(number);

  if (absolute >= 1_000_000_000) {
    return `${(number / 1_000_000_000).toFixed(2)}B`;
  }

  if (absolute >= 1_000_000) {
    return `${(number / 1_000_000).toFixed(2)}M`;
  }

  if (absolute >= 1_000) {
    return `${(number / 1_000).toFixed(1)}K`;
  }

  if (Number.isInteger(number)) {
    return number.toLocaleString();
  }

  return number.toLocaleString(undefined, {
    maximumFractionDigits: 2,
  });
}


/* =========================================================
   DATE FORMATTER
   ========================================================= */

function formatTimeLabel(value) {
  if (!value) {
    return "";
  }

  const stringValue = String(value);

  /*
   * Keep simple Year / Quarter labels readable.
   */
  if (/^\d{4}$/.test(stringValue)) {
    return stringValue;
  }

  if (/^Q[1-4]\s?\d{4}$/i.test(stringValue)) {
    return stringValue;
  }

  /*
   * Try to format ISO date values such as:
   * 2011-01-01
   */
  const date = new Date(stringValue);

  if (!Number.isNaN(date.getTime())) {
    return date.toLocaleDateString("en-US", {
      month: "short",
      year: "numeric",
    });
  }

  return stringValue;
}


/* =========================================================
   FIND ACTUAL OBJECT KEY
   ========================================================= */

function findMatchingKey(row, target) {
  if (!row || !target) {
    return null;
  }

  const normalizedTarget = String(target)
    .toLowerCase()
    .trim();

  return (
    Object.keys(row).find(
      (key) =>
        key.toLowerCase().trim() === normalizedTarget
    ) || null
  );
}


/* =========================================================
   FIND METRIC KEY
   ========================================================= */

function findMetricKey(row, metric) {
  if (!row) {
    return null;
  }

  /*
   * First try exact metric match.
   */
  const exactMatch = findMatchingKey(row, metric);

  if (exactMatch) {
    return exactMatch;
  }

  const normalizedMetric = String(metric || "")
    .toLowerCase()
    .trim();

  /*
   * Sales and Revenue are both represented by
   * FactSales.revenue in the current governed layer.
   */
  if (normalizedMetric === "sales") {
    const revenueKey = findMatchingKey(row, "Revenue");

    if (revenueKey) {
      return revenueKey;
    }
  }

  if (normalizedMetric === "revenue") {
    const salesKey = findMatchingKey(row, "Sales");

    if (salesKey) {
      return salesKey;
    }
  }

  /*
   * Common naming variations.
   */
  const aliases = {
    profit: ["Profit"],
    quantity: ["Quantity", "Quantity Sold"],
    "quantity sold": ["Quantity", "Quantity Sold"],
    "shipping cost": ["Shipping Cost"],
    orders: ["Orders"],
    customers: ["Customers"],
    "profit margin": ["Profit Margin"],
    "average order value": ["Average Order Value"],
  };

  const possibleAliases = aliases[normalizedMetric] || [];

  for (const alias of possibleAliases) {
    const aliasKey = findMatchingKey(row, alias);

    if (aliasKey) {
      return aliasKey;
    }
  }

  return null;
}


/* =========================================================
   FIND TIME DIMENSION
   ========================================================= */

function findTimeDimensionKey(row) {
  if (!row) {
    return null;
  }

  const keys = Object.keys(row);

  /*
   * Prefer Month, Quarter and Year.
   */
  const preferred = [
    "Month",
    "Quarter",
    "Year",
    "Date",
    "Order Date",
  ];

  for (const candidate of preferred) {
    const match = keys.find(
      (key) =>
        key.toLowerCase().trim() ===
        candidate.toLowerCase().trim()
    );

    if (match) {
      return match;
    }
  }

  /*
   * Fallback:
   * detect a date-looking backend key.
   */
  return (
    keys.find((key) => {
      const normalized = key.toLowerCase();

      return (
        normalized.includes("month") ||
        normalized.includes("quarter") ||
        normalized.includes("year") ||
        normalized.includes("date")
      );
    }) || null
  );
}


/* =========================================================
   CHECK TIME DIMENSION
   ========================================================= */

function isTimeDimensionName(name) {
  if (!name) {
    return false;
  }

  const normalized = String(name).toLowerCase();

  return (
    normalized.includes("month") ||
    normalized.includes("date") ||
    normalized.includes("year") ||
    normalized.includes("quarter")
  );
}


/* =========================================================
   CHART RENDERER
   ========================================================= */

function ChartRenderer({
  data,
  metric,
  dimension,
}) {
  if (!Array.isArray(data) || data.length === 0) {
    return null;
  }

  const firstRow = data[0];

  if (!firstRow || typeof firstRow !== "object") {
    return null;
  }


  /* =======================================================
     RESOLVE METRIC
     ======================================================= */

  const metricKey = findMetricKey(
    firstRow,
    metric
  );

  if (!metricKey) {
    return null;
  }


  /* =======================================================
     RESOLVE DIMENSION
     ======================================================= */

  let dimensionKey = findMatchingKey(
    firstRow,
    dimension
  );

  /*
   * Important:
   *
   * Time-series backend responses may have:
   *
   * dimension = null
   *
   * but the actual data contains:
   *
   * Month
   *
   * Therefore infer the time dimension automatically.
   */

  if (!dimensionKey) {
    dimensionKey = findTimeDimensionKey(firstRow);
  }


  if (!dimensionKey) {
    return null;
  }


  /* =======================================================
     DETERMINE CHART TYPE
     ======================================================= */

  const isTimeSeries =
    isTimeDimensionName(dimensionKey) ||
    isTimeDimensionName(dimension);


  /* =======================================================
     VALID ROWS
     ======================================================= */

  const validRows = data.filter((row) => {
    const dimensionValue = row[dimensionKey];
    const metricValue = Number(row[metricKey]);

    return (
      dimensionValue !== undefined &&
      dimensionValue !== null &&
      dimensionValue !== "" &&
      Number.isFinite(metricValue)
    );
  });


  if (validRows.length === 0) {
    return null;
  }


  /* =======================================================
     TIME SERIES
     ======================================================= */

  if (isTimeSeries) {

    /*
     * IMPORTANT:
     *
     * Do NOT limit time-series data to 10 rows.
     *
     * If the backend returns 48 months,
     * all 48 months should be visualized.
     */

    const chartRows = validRows;

    const categories = chartRows.map((row) =>
      formatTimeLabel(row[dimensionKey])
    );

    const values = chartRows.map((row) =>
      Number(row[metricKey])
    );


    const option = {
      backgroundColor: "transparent",

      animation: true,

      tooltip: {
        trigger: "axis",

        backgroundColor: "#171927",
        borderColor: "#34374d",
        borderWidth: 1,

        textStyle: {
          color: "#f8fafc",
          fontSize: 12,
        },

        axisPointer: {
          type: "line",
          lineStyle: {
            color: "#8b5cf6",
            opacity: 0.35,
          },
        },

        formatter: (params) => {
          if (!params || params.length === 0) {
            return "";
          }

          const item = params[0];

          return `
            <div style="
              font-weight:600;
              margin-bottom:6px;
              color:#f8fafc;
            ">
              ${item.axisValue}
            </div>

            <div style="color:#cbd5e1;">
              ${metric || "Value"}:
              <strong style="color:#a78bfa;">
                ${formatNumber(item.value)}
              </strong>
            </div>
          `;
        },
      },


      grid: {
        left: "4%",
        right: "4%",
        top: "12%",
        bottom: "12%",
        containLabel: true,
      },


      xAxis: {
        type: "category",

        data: categories,

        boundaryGap: false,

        axisLabel: {
          color: "#8f97aa",
          fontSize: 10,

          interval:
            categories.length > 24
              ? 3
              : categories.length > 12
              ? 1
              : 0,
        },

        axisLine: {
          lineStyle: {
            color: "#303347",
          },
        },

        axisTick: {
          show: false,
        },
      },


      yAxis: {
        type: "value",

        name: metric || "Value",

        nameTextStyle: {
          color: "#8f97aa",
          fontSize: 10,
        },

        axisLabel: {
          color: "#8f97aa",
          fontSize: 10,

          formatter: (value) =>
            formatNumber(value),
        },

        splitLine: {
          lineStyle: {
            color: "#25283a",
            type: "dashed",
          },
        },

        axisLine: {
          show: false,
        },

        axisTick: {
          show: false,
        },
      },


      series: [
        {
          name: metric || "Value",

          type: "line",

          data: values,

          smooth: true,

          symbol: "circle",
          symbolSize: 6,

          lineStyle: {
            width: 3,
            color: "#8b5cf6",
          },

          itemStyle: {
            color: "#a78bfa",
            borderColor: "#8b5cf6",
            borderWidth: 2,
          },

          areaStyle: {
            color: "#8b5cf6",
            opacity: 0.08,
          },

          emphasis: {
            focus: "series",

            itemStyle: {
              color: "#c4b5fd",
              borderColor: "#8b5cf6",
              borderWidth: 3,
            },
          },
        },
      ],
    };


    return (
      <div
        className="chart-container"
        style={{
          width: "100%",
          height: "360px",
        }}
      >
        <ReactECharts
          option={option}
          style={{
            width: "100%",
            height: "100%",
          }}
          notMerge={true}
          lazyUpdate={true}
        />
      </div>
    );
  }


  /* =======================================================
     CATEGORICAL DATA
     ======================================================= */

  /*
   * Keep top 10 categorical results.
   *
   * Time-series data above is NOT limited.
   */

  const chartRows = validRows.slice(0, 10);

  const categories = chartRows.map((row) =>
    String(row[dimensionKey])
  );

  const values = chartRows.map((row) =>
    Number(row[metricKey])
  );


  /*
   * Reverse so the largest result appears
   * visually toward the top.
   */

  const reversedCategories = [
    ...categories,
  ].reverse();

  const reversedValues = [
    ...values,
  ].reverse();


  /* =======================================================
     HORIZONTAL BAR CHART
     ======================================================= */

  const option = {
    backgroundColor: "transparent",

    animation: true,


    tooltip: {
      trigger: "axis",

      backgroundColor: "#171927",
      borderColor: "#34374d",
      borderWidth: 1,

      textStyle: {
        color: "#f8fafc",
        fontSize: 12,
      },

      axisPointer: {
        type: "shadow",
      },

      formatter: (params) => {
        if (!params || params.length === 0) {
          return "";
        }

        const item = params[0];

        return `
          <div style="
            font-weight:600;
            margin-bottom:6px;
            color:#f8fafc;
          ">
            ${item.name}
          </div>

          <div style="color:#cbd5e1;">
            ${metric || "Value"}:
            <strong style="color:#a78bfa;">
              ${formatNumber(item.value)}
            </strong>
          </div>
        `;
      },
    },


    grid: {
      left: "2%",
      right: "6%",
      top: "7%",
      bottom: "7%",
      containLabel: true,
    },


    xAxis: {
      type: "value",

      name: metric || "Value",

      nameTextStyle: {
        color: "#8f97aa",
        fontSize: 10,
      },

      axisLabel: {
        color: "#8f97aa",
        fontSize: 10,

        formatter: (value) =>
          formatNumber(value),
      },

      splitLine: {
        lineStyle: {
          color: "#25283a",
          type: "dashed",
        },
      },

      axisLine: {
        show: false,
      },

      axisTick: {
        show: false,
      },
    },


    yAxis: {
      type: "category",

      data: reversedCategories,

      axisLabel: {
        color: "#c2c8d6",
        fontSize: 10,

        width: 150,

        overflow: "truncate",

        ellipsis: "...",
      },

      axisLine: {
        show: false,
      },

      axisTick: {
        show: false,
      },
    },


    series: [
      {
        name: metric || "Value",

        type: "bar",

        data: reversedValues,

        barMaxWidth: 24,

        itemStyle: {
          color: "#7c5ce3",

          borderRadius: [
            0,
            6,
            6,
            0,
          ],
        },

        emphasis: {
          focus: "series",

          itemStyle: {
            color: "#9b7cf6",
          },
        },

        label: {
          show: false,
        },
      },
    ],
  };


  return (
    <div
      className="chart-container"
      style={{
        width: "100%",
        height: `${Math.max(
          330,
          chartRows.length * 38 + 80
        )}px`,
      }}
    >
      <ReactECharts
        option={option}
        style={{
          width: "100%",
          height: "100%",
        }}
        notMerge={true}
        lazyUpdate={true}
      />
    </div>
  );
}


export default ChartRenderer;