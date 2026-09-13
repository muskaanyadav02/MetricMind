import {
  BarChart3,
  TrendingUp,
  Package,
  CircleDollarSign,
} from "lucide-react";

import ChartCard from "../components/ChartCard";

import {
  categorySales,
  monthlySales,
  regionSales,
} from "../utils/analytics";

import "./Analytics.css";

function Analytics() {
  return (
    <div className="analytics-page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">ANALYTICS</span>
          <h1>Business Analytics</h1>
          <p>
            Explore sales, profit, category and regional performance.
          </p>
        </div>

        <button className="period-button">
          2024
        </button>
      </div>

      <div className="analytics-summary">
        <div>
          <BarChart3 size={18} />
          <span>Total Sales</span>
          <strong>₹56,591</strong>
        </div>

        <div>
          <CircleDollarSign size={18} />
          <span>Total Profit</span>
          <strong>₹24,813</strong>
        </div>

        <div>
          <Package size={18} />
          <span>Total Orders</span>
          <strong>1,999</strong>
        </div>

        <div>
          <TrendingUp size={18} />
          <span>Growth</span>
          <strong>+12.4%</strong>
        </div>
      </div>

      <div className="analytics-grid">
        <ChartCard
          title="Sales by Category"
          subtitle="Revenue contribution"
          data={categorySales}
          dataKey="sales"
          xKey="category"
          type="bar"
        />

        <ChartCard
          title="Sales by Region"
          subtitle="Regional performance"
          data={regionSales}
          dataKey="sales"
          xKey="category"
          type="bar"
        />

        <ChartCard
          title="Monthly Trends"
          subtitle="Sales movement throughout the year"
          data={monthlySales}
          dataKey="sales"
          xKey="month"
        />

        <ChartCard
          title="Revenue Trend"
          subtitle="Business performance over time"
          data={monthlySales}
          dataKey="sales"
          xKey="month"
        />
      </div>
    </div>
  );
}

export default Analytics;