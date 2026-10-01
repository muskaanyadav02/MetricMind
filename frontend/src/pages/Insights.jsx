
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  ArrowUpRight,
  BarChart3,
  RefreshCw,
  Sparkles,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

import InsightCard from "../components/InsightCard";
import { loadBusinessInsights } from "../utils/businessInsights";
import "./Insights.css";

const formatCurrency = (value) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(Number(value) || 0);

const formatNumber = (value) =>
  new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 1,
  }).format(Number(value) || 0);

const formatPercent = (value) => `${formatNumber(value)}%`;

/*
 * Read the numeric value from insight objects.
 * Different groupings may use different property names:
 * category -> profit, region -> sales, products -> profit.
 *
 * Return null when no numeric value exists instead of
 * incorrectly displaying ₹0.
 */
function getInsightValue(item) {
  if (!item || typeof item !== "object") {
    return null;
  }

  const keys = [
    "value",
    "profit",
    "sales",
    "total",
    "totalProfit",
    "totalSales",
    "total_profit",
    "total_sales",
    "aggregateProfit",
    "aggregateSales",
    "aggregate_profit",
    "aggregate_sales",
    "sum_profit",
    "sum_sales",
    "Profit",
    "Sales",
  ];

  for (const key of keys) {
    const rawValue = item[key];

    if (
      rawValue === null ||
      rawValue === undefined ||
      rawValue === ""
    ) {
      continue;
    }

    const numericValue = Number(rawValue);

    if (Number.isFinite(numericValue)) {
      return numericValue;
    }
  }

  return null;
}

function Insights() {
  const navigate = useNavigate();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchInsights = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const result = await loadBusinessInsights();
      setData(result);
    } catch (err) {
      console.error("Failed to load business insights:", err);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load business insights. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchInsights();
  }, [fetchInsights]);

  const investigate = (question) => {
    navigate("/ask", {
      state: { question },
    });
  };

  if (loading) {
    return (
      <main className="insights-page">
        <header className="insights-header">
          <div>
            <span className="insights-eyebrow">
              DATA-DRIVEN ANALYSIS
            </span>
            <h1>Business Insights</h1>
            <p>
              Evidence-backed observations from your business dataset.
            </p>
          </div>
        </header>

        <div className="insight-state" role="status">
          <RefreshCw className="spin" size={22} />
          <div>
            <h2>Analyzing your business data</h2>
            <p>
              Loading records and calculating business findings...
            </p>
          </div>
        </div>
      </main>
    );
  }

  if (error || !data) {
    return (
      <main className="insights-page">
        <header className="insights-header">
          <div>
            <span className="insights-eyebrow">
              DATA-DRIVEN ANALYSIS
            </span>
            <h1>Business Insights</h1>
            <p>
              Evidence-backed observations from your business dataset.
            </p>
          </div>

          <button
            type="button"
            className="investigate-button"
            onClick={fetchInsights}
          >
            <RefreshCw size={15} />
            Retry
          </button>
        </header>

        <div className="insight-state insight-error" role="alert">
          <AlertTriangle size={24} />
          <div>
            <h2>Insights could not be loaded</h2>
            <p>
              {error || "No insight data is available."}
            </p>
            <button
              type="button"
              className="investigate-button"
              onClick={fetchInsights}
            >
              Try again
            </button>
          </div>
        </div>
      </main>
    );
  }

  const topCategory = data.topCategory;
  const topRegion = data.topRegion;
  const lossProducts = data.lossProducts || [];

  const topCategoryValue = getInsightValue(topCategory);
  const topRegionValue = getInsightValue(topRegion);

  const summaryCards = [
    {
      label: "Total sales",
      value: formatCurrency(data.totalSales),
      description: "Recorded sales across valid dataset rows",
    },
    {
      label: "Total profit",
      value: formatCurrency(data.totalProfit),
      description: "Net recorded profit",
    },
    {
      label: "Profit margin",
      value: formatPercent(data.profitMargin),
      description: "Profit as a percentage of sales",
    },
    {
      label: "Latest month vs previous month",
      value:
        data.monthlyChange == null
          ? "N/A"
          : formatPercent(data.monthlyChange),
      description: "Change in recorded monthly sales",
    },
  ];

  const findings = [
    {
      title: topCategory?.name
        ? `${topCategory.name} leads category profit`
        : "Category profit unavailable",
      description:
        topCategoryValue === null
          ? "The category profit value is unavailable."
          : `Total recorded profit: ${formatCurrency(topCategoryValue)}.`,
      type: "purple",
      time: "Dataset finding",
    },
    {
      title: topRegion?.name
        ? `${topRegion.name} leads regional sales`
        : "Regional sales unavailable",
      description:
        topRegionValue === null
          ? "The regional sales value is unavailable."
          : `Total recorded sales: ${formatCurrency(topRegionValue)}.`,
      type: "blue",
      time: "Dataset finding",
    },
    {
      title: "Products with negative profit",
      description: lossProducts.length
        ? `${lossProducts.length} products appear in the top loss list and may warrant review.`
        : "No negative-profit products were found in the analyzed records.",
      type: "orange",
      time: "Profitability check",
    },
  ];

  return (
    <main className="insights-page">
      <header className="insights-header">
        <div>
          <span className="insights-eyebrow">
            DATA-DRIVEN ANALYSIS
          </span>
          <h1>Business Insights</h1>
          <p>
            Evidence-backed observations from your business dataset.
          </p>
        </div>

        <button
          type="button"
          className="investigate-button"
          onClick={fetchInsights}
          disabled={loading}
        >
          <RefreshCw size={15} />
          Refresh
        </button>
      </header>

      <section className="insights-hero">
        <div className="insights-hero-icon">
          <Sparkles size={24} />
        </div>

        <div>
          <span className="insights-eyebrow">
            EXECUTIVE SUMMARY
          </span>
          <h2>Business performance overview</h2>
          <p>
            Analyzed {formatNumber(data.recordCount)} valid records.
            Total recorded sales are {formatCurrency(data.totalSales)},
            with profit of {formatCurrency(data.totalProfit)} and a
            profit margin of {formatPercent(data.profitMargin)}.
          </p>

          {data.dateRange && (
            <p className="insights-date-range">
              Data period: {data.dateRange.start} to{" "}
              {data.dateRange.end}
            </p>
          )}
        </div>
      </section>

      <section className="insight-grid">
        <article className="insight-card large-insight">
          <div className="insight-card-icon purple">
            <ArrowUpRight size={20} />
          </div>

          <span className="insights-eyebrow">CATEGORY PROFIT</span>
          <h3>{topCategory?.name || "Unavailable"}</h3>
          <p>
            Category with the highest aggregate recorded profit
            in this dataset.
          </p>

          <div className="insight-card-footer">
            <div className="insight-metric">
              <strong>
                {topCategoryValue === null
                  ? "N/A"
                  : formatCurrency(topCategoryValue)}
              </strong>
              <span>total profit</span>
            </div>

            <button
              type="button"
              className="investigate-button"
              onClick={() =>
                investigate("Show total profit by category")
              }
            >
              Investigate <ArrowUpRight size={14} />
            </button>
          </div>
        </article>

        <article className="insight-card large-insight">
          <div className="insight-card-icon blue">
            <BarChart3 size={20} />
          </div>

          <span className="insights-eyebrow">REGIONAL SALES</span>
          <h3>{topRegion?.name || "Unavailable"}</h3>
          <p>
            Region with the highest aggregate recorded sales.
          </p>

          <div className="insight-card-footer">
            <div className="insight-metric">
              <strong>
                {topRegionValue === null
                  ? "N/A"
                  : formatCurrency(topRegionValue)}
              </strong>
              <span>total sales</span>
            </div>

            <button
              type="button"
              className="investigate-button"
              onClick={() =>
                investigate("Show total sales by region")
              }
            >
              Investigate <ArrowUpRight size={14} />
            </button>
          </div>
        </article>

        <article className="insight-card large-insight">
          <div className="insight-card-icon orange">
            <TrendingDown size={20} />
          </div>

          <span className="insights-eyebrow">
            PROFITABILITY ALERT
          </span>
          <h3>Products with negative profit</h3>
          <p>
            These products have negative aggregate profit and may
            warrant review.
          </p>

          <div className="insight-card-footer">
            <div className="insight-metric">
              <strong>{lossProducts.length}</strong>
              <span>products in the top loss list</span>
            </div>

            <button
              type="button"
              className="investigate-button"
              onClick={() =>
                investigate("Show products with negative profit")
              }
            >
              Investigate <ArrowUpRight size={14} />
            </button>
          </div>
        </article>
      </section>

      <section className="insight-summary-grid">
        {summaryCards.map((card) => (
          <article
            className="insight-summary-tile"
            key={card.label}
          >
            <span>{card.label}</span>
            <strong>{card.value}</strong>
            <p>{card.description}</p>
          </article>
        ))}
      </section>

      <section className="recent-insights">
        <div className="section-heading">
          <div>
            <span className="insights-eyebrow">FINDINGS</span>
            <h2>Latest data observations</h2>
          </div>
        </div>

        <div className="recent-insight-list">
          {findings.map((finding) => (
            <InsightCard
              key={finding.title}
              title={finding.title}
              description={finding.description}
              type={finding.type}
              time={finding.time}
            />
          ))}
        </div>

        <div className="loss-product-list">
          <h3>Products with the largest aggregate losses</h3>

          {lossProducts.length > 0 ? (
            lossProducts.map((product, index) => {
              const productValue = getInsightValue(product);

              return (
                <div
                  className="loss-product-row"
                  key={`${product.name || "product"}-${index}`}
                >
                  <span>{product.name || "Unnamed product"}</span>
                  <strong>
                    {productValue === null
                      ? "N/A"
                      : formatCurrency(productValue)}
                  </strong>
                </div>
              );
            })
          ) : (
            <p>No negative-profit products were found.</p>
          )}
        </div>
      </section>

      <p className="insight-disclaimer">
        <TrendingUp size={14} />
        Findings are calculated from available CSV records. They
        are descriptive signals, not proof of causation or future
        business results.
      </p>
    </main>
  );
}

export default Insights;
