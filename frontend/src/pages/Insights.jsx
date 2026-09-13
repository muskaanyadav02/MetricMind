import {
  AlertTriangle,
  ArrowUpRight,
  BarChart3,
  Sparkles,
  TrendingDown,
} from "lucide-react";

import InsightCard from "../components/InsightCard";

import "./Insights.css";

function Insights() {
  return (
    <div className="insights-page">

      <div className="page-heading">
        <div>
          <span className="eyebrow">AI GENERATED</span>
          <h1>Business Insights</h1>
          <p>
            AI-powered observations from your business data.
          </p>
        </div>
      </div>

      <div className="insights-hero">
        <div className="insights-hero-icon">
          <Sparkles size={25} />
        </div>

        <div>
          <span className="eyebrow">EXECUTIVE SUMMARY</span>
          <h2>Your business is trending positively</h2>

          <p>
            Sales are increasing while technology continues to lead
            profitability. A few low-margin regions require attention.
          </p>
        </div>
      </div>

      <div className="insight-grid">

        <div className="large-insight">
          <div className="large-insight-icon purple">
            <ArrowUpRight size={20} />
          </div>

          <span className="eyebrow">PROFITABILITY</span>

          <h3>Technology is the strongest category</h3>

          <p>
            Technology currently contributes the highest profit
            contribution across the major categories.
          </p>

          <div className="insight-metric">
            <strong>₹18,420</strong>
            <span>category sales</span>
          </div>
        </div>

        <div className="large-insight">
          <div className="large-insight-icon blue">
            <BarChart3 size={20} />
          </div>

          <span className="eyebrow">PERFORMANCE</span>

          <h3>Sales performance is improving</h3>

          <p>
            Overall sales have increased compared with the previous
            period.
          </p>

          <div className="insight-metric">
            <strong>+12.4%</strong>
            <span>growth</span>
          </div>
        </div>

        <div className="large-insight warning">
          <div className="large-insight-icon orange">
            <TrendingDown size={20} />
          </div>

          <span className="eyebrow">ATTENTION REQUIRED</span>

          <h3>Review low-profit regions</h3>

          <p>
            Some regions are showing significantly lower profit margins
            and may require further analysis.
          </p>

          <div className="insight-metric">
            <strong>3</strong>
            <span>regions to review</span>
          </div>
        </div>

      </div>

      <div className="recent-insights">
        <div className="section-header">
          <div>
            <span className="eyebrow">RECENT</span>
            <h3>Latest AI observations</h3>
          </div>
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
          title="Low-margin regions detected"
          description="Some regions require deeper profitability analysis."
          time="Yesterday"
          type="orange"
        />
      </div>
    </div>
  );
}

export default Insights;