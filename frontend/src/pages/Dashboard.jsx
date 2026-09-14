import {
  ArrowRight,
  BarChart3,
  Bot,
  CircleDollarSign,
  Package,
  ShoppingCart,
  Sparkles,
} from "lucide-react";

import { Link } from "react-router-dom";

import KpiCard from "../components/KpiCard";
import InsightCard from "../components/InsightCard";
import ChartCard from "../components/ChartCard";

import { monthlySales } from "../utils/analytics";

import "./Dashboard.css";

function Dashboard() {
  return (
    <div className="dashboard-page">

      <div className="page-heading">
        <div>
          <span className="eyebrow">WORKSPACE / DASHBOARD</span>
          <h1>Dashboard</h1>
          <p>Your business intelligence, simplified.</p>
        </div>

        <button className="period-button">
          Last 30 days
        </button>
      </div>

      <section className="hero-banner">
        <div className="hero-content">
          <span className="eyebrow">
            ✦ AI-POWERED BUSINESS INTELLIGENCE
          </span>

          <h2>
            Turn your data into
            <br />
            <span>smarter decisions.</span>
          </h2>

          <p>
            Ask questions about your business data and get reliable,
            actionable insights powered by MetricMind.
          </p>

          <div className="hero-actions">
            <Link to="/ask" className="primary-button">
              <Bot size={16} />
              Ask MetricMind
            </Link>

            <Link to="/analytics" className="secondary-button">
              Explore Analytics
              <ArrowRight size={15} />
            </Link>
          </div>
        </div>

        <div className="hero-visual">
          <div className="floating-stat stat-one">
            <span>Total Sales</span>
            <strong>₹56.6K</strong>
            <small>↑ 12.4%</small>
          </div>

          <div className="floating-stat stat-two">
            <span>Total Profit</span>
            <strong>₹24.8K</strong>
            <small>↑ 8.7%</small>
          </div>

          <div className="hero-chart">
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
          </div>
        </div>
      </section>

      <section className="kpi-grid">
        <KpiCard
          title="Total Revenue"
          value="₹56,591"
          change="+12.4%"
          icon={CircleDollarSign}
          type="purple"
        />

        <KpiCard
          title="Total Profit"
          value="₹24,813"
          change="+8.7%"
          icon={CircleDollarSign}
          type="green"
        />

        <KpiCard
          title="Total Orders"
          value="1,999"
          change="+4.2%"
          icon={ShoppingCart}
          type="blue"
        />

        <KpiCard
          title="Avg. Order Value"
          value="₹28.31"
          change="+4.7%"
          icon={Package}
          type="orange"
        />
      </section>

      <section className="dashboard-two-column">

        <div className="assistant-card">
          <div className="card-heading">
            <div>
              <span className="eyebrow">✦ AI ASSISTANT</span>
              <h3>Ask MetricMind anything about your business</h3>
              <p>
                Get instant answers, deep analysis, and actionable insights.
              </p>
            </div>

            <span className="online-status">
              <span />
              Online
            </span>
          </div>

          <Link to="/ask" className="assistant-input">
            <Bot size={17} />
            <span>
              Ask a question... e.g. Which category made the most profit?
            </span>

            <ArrowRight size={16} />
          </Link>

          <div className="suggestions">
            <span>Highest profit category</span>
            <span>Sales by country</span>
            <span>Lowest quantity region</span>
            <span>Show sales trend</span>
          </div>
        </div>

        <div className="latest-insights">
          <div className="section-header">
            <div>
              <span className="eyebrow">✦ AI GENERATED</span>
              <h3>Latest Insights</h3>
            </div>

            <Link to="/insights">
              View all <ArrowRight size={13} />
            </Link>
          </div>

          <InsightCard
            title="Technology leads profitability"
            description="Technology generated the strongest profit contribution."
            time="2 hours ago"
            type="purple"
          />

          <InsightCard
            title="Sales performance improved"
            description="Overall sales increased compared with the previous period."
            time="5 hours ago"
            type="blue"
          />

          <InsightCard
            title="Review low-profit regions"
            description="Some regions are showing significantly lower profit margins."
            time="Yesterday"
            type="orange"
          />
        </div>
      </section>

      <section className="dashboard-chart-section">
        <ChartCard
          title="Sales Performance"
          subtitle="Monthly sales trend across the business"
          data={monthlySales}
          dataKey="sales"
          xKey="month"
        />
      </section>

      <section className="bottom-stat-grid">
        <div className="bottom-stat">
          <div className="stat-icon purple">
            <Sparkles size={17} />
          </div>

          <div>
            <span>TOP CATEGORY</span>
            <strong>Technology</strong>
          </div>

          <b>₹18,420</b>
        </div>

        <div className="bottom-stat">
          <div className="stat-icon blue">
            <BarChart3 size={17} />
          </div>

          <div>
            <span>TOP REGION</span>
            <strong>Western Europe</strong>
          </div>

          <b>₹14,860</b>
        </div>

        <div className="bottom-stat confidence">
          <div className="stat-icon green">
            <Sparkles size={17} />
          </div>

          <div>
            <span>AI CONFIDENCE</span>
            <strong>94.8%</strong>
          </div>

          <div className="confidence-bar">
            <span />
          </div>
        </div>
      </section>
    </div>
  );
}

export default Dashboard;