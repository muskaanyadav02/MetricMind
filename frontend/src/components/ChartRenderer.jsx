import React from "react";
import ReactECharts from "echarts-for-react";

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

function ChartRenderer({ data, metric, dimension }) {
  if (!Array.isArray(data) || data.length === 0) {
    return null;
  }

  if (!metric || !dimension) {
    return null;
  }

  const firstRow = data[0];

  if (!firstRow || typeof firstRow !== "object") {
    return null;
  }

  /*
   * Find the actual backend keys.
   *
   * Example:
   * dimension = "Country"
   * backend key = "Country"
   *
   * Or:
   * dimension = "Product Name"
   * backend key = "Product Name"
   */
  const dimensionKey =
    Object.keys(firstRow).find(
      (key) =>
        key.toLowerCase().trim() ===
        dimension.toLowerCase().trim()
    ) || dimension;

  const metricKey =
    Object.keys(firstRow).find(
      (key) =>
        key.toLowerCase().trim() ===
        metric.toLowerCase().trim()
    ) || metric;

  /*
   * Keep only rows that actually contain
   * both dimension and metric values.
   */
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

  /*
   * We only visualize the first 10 results.
   *
   * The backend can still return all 100 rows.
   * AskAI.jsx passes the first 10 to this component,
   * but keeping this slice here also protects the component
   * if it is reused somewhere else.
   */
  const chartRows = validRows.slice(0, 10);

  const categories = chartRows.map((row) =>
    String(row[dimensionKey])
  );

  const values = chartRows.map((row) =>
    Number(row[metricKey])
  );

  /*
   * Detect time-based dimensions.
   *
   * These should use a line chart rather than
   * a categorical horizontal bar chart.
   */
  const dimensionName = dimension.toLowerCase();

  const isTimeDimension =
    dimensionName.includes("month") ||
    dimensionName.includes("date") ||
    dimensionName.includes("year") ||
    dimensionName.includes("quarter");

  /*
   * ============================
   * TIME SERIES → LINE CHART
   * ============================
   */
  if (isTimeDimension) {
    const option = {
      animation: true,

      tooltip: {
        trigger: "axis",

        formatter: (params) => {
          if (!params || params.length === 0) {
            return "";
          }

          const item = params[0];

          return `
            <div style="font-weight:600;margin-bottom:4px;">
              ${item.axisValue}
            </div>
            <div>
              ${metric}: <strong>${formatNumber(
            item.value
          )}</strong>
            </div>
          `;
        },
      },

      grid: {
        left: "8%",
        right: "5%",
        top: "15%",
        bottom: "16%",
        containLabel: true,
      },

      xAxis: {
        type: "category",
        data: categories,

        boundaryGap: false,

        axisLabel: {
          color: "#8f90a3",
          fontSize: 10,
          interval: categories.length > 8 ? 1 : 0,
        },

        axisLine: {
          lineStyle: {
            color: "#343544",
          },
        },

        axisTick: {
          show: false,
        },
      },

      yAxis: {
        type: "value",

        name: metric,

        nameTextStyle: {
          color: "#8f90a3",
          fontSize: 10,
        },

        axisLabel: {
          color: "#8f90a3",
          fontSize: 10,

          formatter: (value) =>
            formatNumber(value),
        },

        splitLine: {
          lineStyle: {
            color: "#2c2d3a",
            type: "solid",
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
          name: metric,
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
            color: "#8b5cf6",
          },

          areaStyle: {
            opacity: 0.08,
            color: "#8b5cf6",
          },

          emphasis: {
            focus: "series",
          },
        },
      ],
    };

    return (
      <div
        className="chart-container"
        style={{
          width: "100%",
          height: "320px",
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

  /*
   * ============================
   * CATEGORICAL → HORIZONTAL BAR
   * ============================
   *
   * Horizontal bars are much easier to read
   * for countries, products and categories.
   */

  /*
   * Reverse data so the largest value appears
   * at the top of the chart.
   */
  const reversedCategories = [...categories].reverse();
  const reversedValues = [...values].reverse();

  const option = {
    animation: true,

    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: "shadow",
      },

      formatter: (params) => {
        if (!params || params.length === 0) {
          return "";
        }

        const item = params[0];

        return `
          <div style="font-weight:600;margin-bottom:4px;">
            ${item.name}
          </div>
          <div>
            ${metric}: <strong>${formatNumber(
          item.value
        )}</strong>
          </div>
        `;
      },
    },

    grid: {
      left: "4%",
      right: "7%",
      top: "7%",
      bottom: "7%",
      containLabel: true,
    },

    xAxis: {
      type: "value",

      name: metric,

      nameTextStyle: {
        color: "#8f90a3",
        fontSize: 10,
      },

      axisLabel: {
        color: "#8f90a3",
        fontSize: 10,

        formatter: (value) =>
          formatNumber(value),
      },

      splitLine: {
        lineStyle: {
          color: "#2c2d3a",
          type: "solid",
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
        color: "#aaaabd",
        fontSize: 10,

        width: 130,

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
        name: metric,

        type: "bar",

        data: reversedValues,

        barMaxWidth: 24,

        itemStyle: {
          color: "#5b7be1",

          borderRadius: [0, 4, 4, 0],
        },

        emphasis: {
          focus: "series",

          itemStyle: {
            color: "#7c8ff0",
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
        height: "330px",
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