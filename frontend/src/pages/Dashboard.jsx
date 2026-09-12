import {
  Search,
  Bell,
  Settings,
  Sparkles,
  LayoutDashboard,
  BarChart3,
  Lightbulb,
  FileText,
  Brain,
  TrendingUp,
  ShoppingCart,
  Wallet,
  Trophy,
  MapPin,
  ArrowUpRight,
  ArrowRight,
  ChevronDown,
  Menu,
  X,
  Moon,
  Zap,
  Target,
  Activity,
} from "lucide-react";

import {
  AreaChart,
  Area,
  LineChart,
  Line,
  ResponsiveContainer,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

import { useState } from "react";


// ============================================================
// MOCK DATA
// Easy to replace with your real dataset later
// ============================================================

const salesData = [
  { month: "Jan", sales: 32000 },
  { month: "Feb", sales: 33500 },
  { month: "Mar", sales: 37000 },
  { month: "Apr", sales: 35500 },
  { month: "May", sales: 41000 },
  { month: "Jun", sales: 39500 },
  { month: "Jul", sales: 44500 },
  { month: "Aug", sales: 43000 },
  { month: "Sep", sales: 48500 },
  { month: "Oct", sales: 47000 },
  { month: "Nov", sales: 52500 },
  { month: "Dec", sales: 56591 },
];

const sparkRevenue = [
  { value: 30 },
  { value: 35 },
  { value: 32 },
  { value: 42 },
  { value: 40 },
  { value: 49 },
  { value: 55 },
];

const sparkProfit = [
  { value: 25 },
  { value: 30 },
  { value: 29 },
  { value: 36 },
  { value: 39 },
  { value: 44 },
  { value: 49 },
];

const sparkOrders = [
  { value: 20 },
  { value: 24 },
  { value: 22 },
  { value: 31 },
  { value: 34 },
  { value: 37 },
  { value: 42 },
];

const sparkAov = [
  { value: 18 },
  { value: 20 },
  { value: 24 },
  { value: 23 },
  { value: 28 },
  { value: 30 },
  { value: 34 },
];


// ============================================================
// KPI CARD
// ============================================================

function KpiCard({
  icon: Icon,
  label,
  value,
  change,
  color,
  data,
}) {
  return (
    <div className="kpi-card">
      <div className="kpi-top">
        <div className={`kpi-icon ${color}`}>
          <Icon size={17} />
        </div>

        <div className="kpi-menu">
          <span>•••</span>
        </div>
      </div>

      <div className="kpi-label">{label}</div>

      <div className="kpi-value">{value}</div>

      <div className="kpi-bottom">
        <span className="positive">
          <TrendingUp size={11} />
          {change}
        </span>

        <span className="period">vs last period</span>
      </div>

      <div className="sparkline">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <Line
              type="monotone"
              dataKey="value"
              stroke={color === "green" ? "#22c55e" : color === "blue" ? "#3b82f6" : color === "orange" ? "#f59e0b" : "#a855f7"}
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}


// ============================================================
// SIDEBAR
// ============================================================

function Sidebar({ mobileOpen, setMobileOpen }) {
  const [active, setActive] = useState("Dashboard");

  const menu = [
    {
      name: "Dashboard",
      icon: LayoutDashboard,
    },
    {
      name: "Ask MetricMind",
      icon: Sparkles,
      ai: true,
    },
    {
      name: "Analytics",
      icon: BarChart3,
    },
    {
      name: "Insights",
      icon: Lightbulb,
    },
    {
      name: "Reports",
      icon: FileText,
    },
  ];

  return (
    <>
      {mobileOpen && (
        <div
          className="mobile-overlay"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <aside className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`}>

        <div className="sidebar-header">
          <div className="brand-icon">
            <span>M</span>
          </div>

          <div>
            <div className="brand-name">MetricMind</div>
            <div className="brand-subtitle">
              AI Business Intelligence
            </div>
          </div>

          <button
            className="mobile-close"
            onClick={() => setMobileOpen(false)}
          >
            <X size={20} />
          </button>
        </div>


        <div className="workspace-label">
          WORKSPACE
        </div>

        <div className="workspace-selector">
          <div className="status-dot" />
          <span>Global Superstore</span>
          <ChevronDown size={14} />
        </div>


        <div className="menu-label">
          MAIN MENU
        </div>

        <nav className="sidebar-menu">

          {menu.map((item) => {
            const Icon = item.icon;

            return (
              <button
                key={item.name}
                className={`nav-item ${
                  active === item.name ? "active" : ""
                }`}
                onClick={() => {
                  setActive(item.name);
                  setMobileOpen(false);
                }}
              >
                <Icon size={17} />

                <span>{item.name}</span>

                {item.ai && (
                  <span className="ai-badge">
                    AI
                  </span>
                )}
              </button>
            );
          })}

        </nav>


        <div className="sidebar-spacer" />


        <div className="upgrade-card">

          <div className="upgrade-glow" />

          <div className="upgrade-icon">
            <Sparkles size={17} />
          </div>

          <h4>
            Smarter Insights.
            <br />
            Bigger Decisions.
          </h4>

          <p>
            Unlock advanced AI analysis and
            deeper business intelligence.
          </p>

          <button>
            Upgrade to Pro
            <ArrowRight size={13} />
          </button>

        </div>


        <button className="settings-link">
          <Settings size={15} />
          Settings
        </button>


        <div className="profile">

          <div className="profile-avatar">
            MY
          </div>

          <div className="profile-info">
            <strong>Muskaan Yadav</strong>
            <span>AI Agent Engineer</span>
          </div>

          <span className="profile-dots">
            •••
          </span>

        </div>

      </aside>
    </>
  );
}


// ============================================================
// TOP NAVBAR
// ============================================================

function Navbar({ setMobileOpen }) {
  return (
    <header className="navbar">

      <button
        className="hamburger"
        onClick={() => setMobileOpen(true)}
      >
        <Menu size={22} />
      </button>

      <div className="breadcrumb">
        <span>Workspace</span>
        <span>/</span>
        <strong>Dashboard</strong>
      </div>


      <div className="navbar-actions">

        <div className="search-box">
          <Search size={15} />

          <input
            placeholder="Search anything..."
          />

          <span className="shortcut">
            ⌘ K
          </span>
        </div>

        <button className="icon-button">
          <Moon size={16} />
        </button>

        <button className="icon-button notification">
          <Bell size={16} />
          <span />
        </button>

        <div className="nav-avatar">
          MY
        </div>

      </div>

    </header>
  );
}


// ============================================================
// HERO BANNER
// ============================================================

function HeroBanner() {
  return (
    <section className="hero">

      <div className="hero-grid" />

      <div className="hero-orb orb-one" />
      <div className="hero-orb orb-two" />

      <div className="hero-content">

        <div className="eyebrow">
          <Sparkles size={12} />
          AI-POWERED BUSINESS INTELLIGENCE
        </div>

        <h1>
          Turn your data into
          <br />
          <span>smarter decisions.</span>
        </h1>

        <p>
          Ask questions about your business data and get
          reliable, actionable insights powered by MetricMind.
        </p>

        <div className="hero-buttons">

          <button className="primary-button">
            <Sparkles size={14} />
            Ask MetricMind
          </button>

          <button className="secondary-button">
            Explore Analytics
            <ArrowRight size={14} />
          </button>

        </div>

      </div>


      <div className="floating-stat profit-stat">
        <span>Profit</span>
        <strong>₹24.8K</strong>
        <small>↗ 8.7%</small>
      </div>


      <div className="floating-stat sales-stat">
        <span>Sales</span>
        <strong>₹56.6K</strong>
        <small>↗ 12.4%</small>
      </div>


      <div className="mini-chart">

        <div className="mini-bars">
          <i />
          <i />
          <i />
          <i />
          <i />
          <i />
          <i />
        </div>

        <span>Business performance</span>

      </div>


      <div className="ai-powered-badge">
        <span className="live-dot" />
        Real-time insights · Powered by AI
      </div>

    </section>
  );
}


// ============================================================
// AI ASSISTANT
// ============================================================

function AiAssistant() {
  const suggestions = [
    "Highest profit category",
    "Sales by country",
    "Lowest quantity region",
    "Show sales trend",
  ];

  return (
    <div className="panel assistant-panel">

      <div className="panel-header">

        <div>
          <div className="eyebrow purple">
            <Sparkles size={11} />
            AI ASSISTANT
          </div>

          <h3>
            Ask MetricMind anything
            <br />
            about your business
          </h3>
        </div>

        <div className="online">
          <span />
          Online
        </div>

      </div>

      <p className="panel-description">
        Ask a business question in natural language.
        MetricMind will analyze your data and find the answer.
      </p>


      <div className="question-box">

        <div className="question-input">
          <Sparkles size={14} />

          <span>
            Type your question here...
            <br />
            <small>
              e.g. Which category made the most profit?
            </small>
          </span>
        </div>

        <button className="ask-button">
          Ask
          <ArrowRight size={13} />
        </button>

      </div>


      <div className="try-row">

        <span>Try asking:</span>

        {suggestions.map((suggestion) => (
          <button key={suggestion}>
            {suggestion}
          </button>
        ))}

      </div>

    </div>
  );
}


// ============================================================
// INSIGHTS PANEL
// ============================================================

function InsightsPanel() {

  const insights = [
    {
      icon: TrendingUp,
      title: "Technology leads profitability",
      text: "Technology generated the highest profit margin across categories.",
      time: "2 hours ago",
      color: "purple",
    },
    {
      icon: BarChart3,
      title: "Sales performance improved",
      text: "Overall sales increased compared with the previous period.",
      time: "5 hours ago",
      color: "blue",
    },
    {
      icon: Target,
      title: "Review low-profit regions",
      text: "Several regions are showing significantly lower profit margins.",
      time: "Yesterday",
      color: "orange",
    },
  ];

  return (
    <div className="panel insights-panel">

      <div className="panel-header">

        <div>
          <div className="eyebrow purple">
            <Sparkles size={11} />
            AI GENERATED
          </div>

          <h3>Latest Insights</h3>
        </div>

        <button className="view-all">
          View all
          <ArrowRight size={12} />
        </button>

      </div>


      <div className="insight-list">

        {insights.map((item) => {
          const Icon = item.icon;

          return (
            <div className="insight-item" key={item.title}>

              <div className={`insight-icon ${item.color}`}>
                <Icon size={14} />
              </div>

              <div className="insight-content">

                <strong>
                  {item.title}
                </strong>

                <p>
                  {item.text}
                </p>

                <span>
                  {item.time}
                </span>

              </div>

            </div>
          );
        })}

      </div>

    </div>
  );
}


// ============================================================
// SALES CHART
// ============================================================

function SalesPerformance() {

  const [range, setRange] = useState("12M");

  return (
    <div className="panel sales-panel">

      <div className="sales-header">

        <div>

          <div className="eyebrow purple">
            <Activity size={11} />
            BUSINESS OVERVIEW
          </div>

          <div className="sales-title-row">
            <h2>Sales Performance</h2>

            <span className="sales-growth">
              +12.4%
            </span>
          </div>

          <div className="sales-total">
            ₹56,591
          </div>

        </div>


        <div className="range-buttons">

          {["7D", "30D", "12M"].map((item) => (
            <button
              key={item}
              className={range === item ? "selected" : ""}
              onClick={() => setRange(item)}
            >
              {item}
            </button>
          ))}

        </div>

      </div>


      <div className="chart-container">

        <ResponsiveContainer width="100%" height="100%">

          <AreaChart data={salesData}>

            <defs>

              <linearGradient
                id="salesGradient"
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop
                  offset="0%"
                  stopColor="#a855f7"
                  stopOpacity={0.42}
                />

                <stop
                  offset="100%"
                  stopColor="#7c3aed"
                  stopOpacity={0}
                />
              </linearGradient>

            </defs>

            <CartesianGrid
              stroke="#262638"
              strokeDasharray="3 5"
              vertical={false}
            />

            <XAxis
              dataKey="month"
              stroke="#68687a"
              tickLine={false}
              axisLine={false}
              tick={{ fontSize: 11 }}
            />

            <YAxis
              stroke="#68687a"
              tickLine={false}
              axisLine={false}
              tick={{ fontSize: 10 }}
              tickFormatter={(value) =>
                `₹${Math.round(value / 1000)}K`
              }
              width={45}
            />

            <Tooltip
              contentStyle={{
                background: "#171722",
                border: "1px solid #35334a",
                borderRadius: "10px",
                color: "#fff",
              }}
              formatter={(value) => [
                `₹${Number(value).toLocaleString("en-IN")}`,
                "Sales",
              ]}
            />

            <Area
              type="monotone"
              dataKey="sales"
              stroke="#a855f7"
              strokeWidth={3}
              fill="url(#salesGradient)"
              dot={{
                r: 3,
                fill: "#a855f7",
                stroke: "#0a0a0f",
                strokeWidth: 2,
              }}
              activeDot={{
                r: 6,
              }}
            />

          </AreaChart>

        </ResponsiveContainer>

      </div>

    </div>
  );
}


// ============================================================
// SUMMARY CARDS
// ============================================================

function SummaryCards() {

  return (
    <div className="summary-grid">

      <div className="summary-card">

        <div className="summary-icon purple">
          <Trophy size={17} />
        </div>

        <div className="summary-info">

          <span>TOP CATEGORY</span>

          <strong>Technology</strong>

          <p>
            ₹18,420 · 18.2% profit contribution
          </p>

        </div>

        <ArrowUpRight size={16} />

      </div>


      <div className="summary-card">

        <div className="summary-icon blue">
          <MapPin size={17} />
        </div>

        <div className="summary-info">

          <span>TOP REGION</span>

          <strong>Western Europe</strong>

          <p>
            ₹14,860 · 9.8% from last period
          </p>

        </div>

        <ArrowUpRight size={16} />

      </div>


      <div className="summary-card">

        <div className="summary-icon green">
          <Brain size={17} />
        </div>

        <div className="summary-info">

          <span>AI CONFIDENCE</span>

          <strong>94.8%</strong>

          <p>
            High confidence in current insights
          </p>

          <div className="confidence-bar">
            <div />
          </div>

        </div>

      </div>

    </div>
  );
}


// ============================================================
// RIGHT SIDEBAR
// ============================================================

function RightSidebar() {

  const insights = [
    {
      color: "purple",
      title: "Technology category top performer",
      text: "Technology contributes 18.2% of total profit.",
      time: "2h ago",
    },
    {
      color: "green",
      title: "Western Europe leads sales",
      text: "Sales are up 9.8% compared with the last period.",
      time: "4h ago",
    },
    {
      color: "orange",
      title: "Furniture needs attention",
      text: "Furniture is showing the lowest profit margin.",
      time: "6h ago",
    },
    {
      color: "blue",
      title: "Sales momentum is positive",
      text: "Overall sales are up 12.4% this period.",
      time: "Yesterday",
    },
  ];

  return (
    <aside className="right-sidebar">

      <div className="right-title">

        <div>
          <div className="eyebrow purple">
            <Sparkles size={11} />
            AI-POWERED HIGHLIGHTS
          </div>

          <h3>
            Key Insights
          </h3>
        </div>

        <button>
          <ArrowRight size={14} />
        </button>

      </div>


      <div className="right-insights">

        {insights.map((item) => (
          <div className="right-insight" key={item.title}>

            <div className={`right-dot ${item.color}`} />

            <div>

              <strong>
                {item.title}
              </strong>

              <p>
                {item.text}
              </p>

              <span>
                {item.time}
              </span>

            </div>

          </div>
        ))}

      </div>


      <div className="advanced-card">

        <div className="advanced-icon">
          <Brain size={20} />
        </div>

        <h3>
          Need deeper analysis?
        </h3>

        <p>
          Let AI uncover patterns,
          opportunities and hidden risks.
        </p>

        <button>
          Try Advanced AI
          <ArrowRight size={13} />
        </button>

      </div>

    </aside>
  );
}


// ============================================================
// MAIN DASHBOARD
// ============================================================

function Dashboard() {

  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      <style>{`

        * {
          box-sizing: border-box;
        }

        body {
          margin: 0;
          background: #08090e;
          color: #f5f3ff;
          font-family:
            Inter,
            ui-sans-serif,
            system-ui,
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            sans-serif;
        }

        button,
        input {
          font: inherit;
        }

        button {
          cursor: pointer;
        }


        /* =========================
           APP
        ========================= */

        .metricmind-app {
          min-height: 100vh;
          background:
            radial-gradient(
              circle at 70% -10%,
              rgba(124, 58, 237, 0.09),
              transparent 30%
            ),
            #08090e;
          display: flex;
        }


        /* =========================
           SIDEBAR
        ========================= */

        .sidebar {
          width: 245px;
          min-width: 245px;
          height: 100vh;
          position: fixed;
          left: 0;
          top: 0;
          z-index: 50;
          background: rgba(10, 11, 17, 0.97);
          border-right: 1px solid #20212c;
          display: flex;
          flex-direction: column;
          padding: 22px 15px 16px;
        }

        .sidebar-header {
          display: flex;
          align-items: center;
          gap: 11px;
          padding: 0 5px 26px;
        }

        .brand-icon {
          width: 34px;
          height: 34px;
          border-radius: 10px;
          background:
            linear-gradient(
              135deg,
              #7c3aed,
              #a855f7
            );
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow:
            0 0 25px rgba(139, 92, 246, 0.35);
        }

        .brand-icon span {
          font-size: 17px;
          font-weight: 900;
          color: white;
        }

        .brand-name {
          font-size: 15px;
          font-weight: 750;
          letter-spacing: -0.3px;
        }

        .brand-subtitle {
          font-size: 7px;
          color: #666678;
          margin-top: 3px;
          letter-spacing: 0.5px;
          text-transform: uppercase;
        }

        .workspace-label,
        .menu-label {
          color: #505064;
          font-size: 8px;
          letter-spacing: 1.5px;
          font-weight: 700;
          margin: 7px 8px;
        }

        .workspace-selector {
          height: 43px;
          border: 1px solid #292a37;
          background: #11121a;
          border-radius: 10px;
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 0 10px;
          font-size: 11px;
          color: #dedce9;
          margin-bottom: 27px;
        }

        .workspace-selector svg {
          margin-left: auto;
          color: #656578;
        }

        .status-dot {
          width: 6px;
          height: 6px;
          background: #22c55e;
          border-radius: 50%;
          box-shadow: 0 0 8px rgba(34,197,94,.7);
        }

        .sidebar-menu {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .nav-item {
          height: 39px;
          border: 0;
          background: transparent;
          color: #7e7e91;
          border-radius: 8px;
          display: flex;
          align-items: center;
          gap: 11px;
          padding: 0 11px;
          text-align: left;
          font-size: 11px;
          transition: .2s ease;
        }

        .nav-item:hover {
          color: white;
          background: #151520;
        }

        .nav-item.active {
          color: white;
          background:
            linear-gradient(
              90deg,
              rgba(124,58,237,.23),
              rgba(124,58,237,.08)
            );
          border-left: 2px solid #9b5cff;
          box-shadow:
            inset 0 0 20px rgba(124,58,237,.06);
        }

        .ai-badge {
          margin-left: auto;
          font-size: 7px;
          padding: 3px 5px;
          border-radius: 4px;
          background: #3b1c74;
          color: #c59aff;
        }

        .sidebar-spacer {
          flex: 1;
        }

        .upgrade-card {
          position: relative;
          overflow: hidden;
          border: 1px solid #35235a;
          border-radius: 12px;
          padding: 14px;
          background:
            linear-gradient(
              145deg,
              rgba(74,38,126,.34),
              rgba(18,15,30,.8)
            );
          margin-bottom: 15px;
        }

        .upgrade-glow {
          position: absolute;
          width: 90px;
          height: 90px;
          border-radius: 50%;
          background: #7c3aed;
          filter: blur(50px);
          opacity: .15;
          top: -45px;
          right: -20px;
        }

        .upgrade-icon {
          width: 29px;
          height: 29px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(139,92,246,.15);
          color: #bd8cff;
          margin-bottom: 10px;
        }

        .upgrade-card h4 {
          margin: 0 0 7px;
          font-size: 12px;
          line-height: 1.4;
        }

        .upgrade-card p {
          color: #77778a;
          font-size: 9px;
          line-height: 1.55;
          margin: 0 0 12px;
        }

        .upgrade-card button {
          width: 100%;
          height: 29px;
          border: 0;
          border-radius: 7px;
          color: white;
          font-size: 9px;
          font-weight: 700;
          background:
            linear-gradient(
              135deg,
              #7c3aed,
              #a855f7
            );
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          box-shadow:
            0 7px 20px rgba(124,58,237,.25);
        }

        .settings-link {
          border: 0;
          background: transparent;
          color: #686879;
          display: flex;
          align-items: center;
          gap: 9px;
          padding: 8px 8px 13px;
          font-size: 10px;
        }

        .profile {
          border-top: 1px solid #20212b;
          padding-top: 13px;
          display: flex;
          align-items: center;
          gap: 9px;
        }

        .profile-avatar,
        .nav-avatar {
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: 800;
          background:
            linear-gradient(
              135deg,
              #7c3aed,
              #a855f7
            );
        }

        .profile-avatar {
          width: 29px;
          height: 29px;
          border-radius: 8px;
          font-size: 8px;
        }

        .profile-info {
          display: flex;
          flex-direction: column;
          gap: 2px;
          min-width: 0;
        }

        .profile-info strong {
          font-size: 9px;
        }

        .profile-info span {
          color: #666678;
          font-size: 7px;
        }

        .profile-dots {
          margin-left: auto;
          color: #555568;
          font-size: 10px;
        }

        .mobile-close {
          display: none;
        }


        /* =========================
           MAIN
        ========================= */

        .main-wrapper {
          margin-left: 245px;
          width: calc(100% - 245px);
          min-height: 100vh;
        }

        .main-content {
          width: min(1180px, calc(100% - 50px));
          margin: auto;
          padding-bottom: 50px;
        }


        /* =========================
           NAVBAR
        ========================= */

        .navbar {
          height: 70px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          border-bottom: 1px solid #181923;
          margin-bottom: 25px;
        }

        .breadcrumb {
          display: flex;
          gap: 8px;
          font-size: 9px;
          color: #565668;
        }

        .breadcrumb strong {
          color: #aaa8ba;
        }

        .navbar-actions {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .search-box {
          height: 34px;
          width: 245px;
          border: 1px solid #292a37;
          background: #101119;
          border-radius: 8px;
          display: flex;
          align-items: center;
          padding: 0 9px;
          gap: 7px;
          color: #626275;
        }

        .search-box input {
          flex: 1;
          min-width: 0;
          background: transparent;
          border: 0;
          outline: 0;
          color: white;
          font-size: 9px;
        }

        .search-box input::placeholder {
          color: #5d5d70;
        }

        .shortcut {
          border: 1px solid #292a37;
          background: #171821;
          border-radius: 4px;
          padding: 3px 5px;
          color: #666678;
          font-size: 8px;
        }

        .icon-button {
          position: relative;
          width: 34px;
          height: 34px;
          border: 1px solid #292a37;
          background: #101119;
          border-radius: 8px;
          color: #858597;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .notification span {
          position: absolute;
          width: 5px;
          height: 5px;
          background: #ef4444;
          border-radius: 50%;
          top: 7px;
          right: 7px;
          border: 1px solid #101119;
        }

        .nav-avatar {
          width: 34px;
          height: 34px;
          border-radius: 9px;
          font-size: 8px;
        }

        .hamburger {
          display: none;
        }


        /* =========================
           HERO
        ========================= */

        .hero {
          position: relative;
          min-height: 260px;
          overflow: hidden;
          border: 1px solid #34284e;
          border-radius: 17px;
          background:
            radial-gradient(
              circle at 80% 45%,
              rgba(124,58,237,.22),
              transparent 30%
            ),
            linear-gradient(
              110deg,
              #101018,
              #161020,
              #100e17
            );
          margin-bottom: 15px;
        }

        .hero-grid {
          position: absolute;
          inset: 0;
          opacity: .16;
          background-image:
            linear-gradient(#a855f7 1px, transparent 1px),
            linear-gradient(90deg, #a855f7 1px, transparent 1px);
          background-size: 36px 36px;
          mask-image: linear-gradient(
            90deg,
            black,
            transparent 85%
          );
        }

        .hero-orb {
          position: absolute;
          border: 1px solid rgba(168,85,247,.15);
          border-radius: 50%;
        }

        .orb-one {
          width: 300px;
          height: 300px;
          right: -15px;
          top: -90px;
        }

        .orb-two {
          width: 220px;
          height: 220px;
          right: 40px;
          top: -50px;
        }

        .hero-content {
          position: relative;
          z-index: 2;
          padding: 39px 37px;
          max-width: 630px;
        }

        .eyebrow {
          display: flex;
          align-items: center;
          gap: 5px;
          color: #b66cff;
          font-size: 7px;
          font-weight: 800;
          letter-spacing: 1.4px;
          margin-bottom: 12px;
        }

        .eyebrow.purple {
          color: #aa62ff;
        }

        .hero h1 {
          font-size: clamp(28px, 3vw, 43px);
          line-height: 1.02;
          letter-spacing: -1.8px;
          margin: 0 0 14px;
          font-weight: 780;
        }

        .hero h1 span {
          background:
            linear-gradient(
              90deg,
              #a855f7,
              #818cf8,
              #c084fc
            );
          -webkit-background-clip: text;
          background-clip: text;
          color: transparent;
        }

        .hero p {
          max-width: 510px;
          color: #777789;
          font-size: 10px;
          line-height: 1.7;
          margin-bottom: 22px;
        }

        .hero-buttons {
          display: flex;
          gap: 8px;
        }

        .primary-button,
        .secondary-button {
          height: 36px;
          padding: 0 14px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          gap: 7px;
          font-size: 9px;
          font-weight: 700;
        }

        .primary-button {
          color: white;
          border: 0;
          background:
            linear-gradient(
              135deg,
              #7c3aed,
              #a855f7
            );
          box-shadow:
            0 8px 28px rgba(124,58,237,.35);
        }

        .secondary-button {
          color: #bbb9c9;
          background: rgba(20,20,29,.7);
          border: 1px solid #393344;
        }

        .floating-stat {
          position: absolute;
          z-index: 4;
          background: rgba(17,16,25,.76);
          backdrop-filter: blur(12px);
          border: 1px solid #393047;
          border-radius: 10px;
          padding: 11px 13px;
          box-shadow: 0 15px 40px rgba(0,0,0,.25);
        }

        .floating-stat span,
        .floating-stat small {
          display: block;
        }

        .floating-stat span {
          color: #666577;
          font-size: 7px;
          margin-bottom: 5px;
        }

        .floating-stat strong {
          display: block;
          font-size: 15px;
          margin-bottom: 3px;
        }

        .floating-stat small {
          color: #22c55e;
          font-size: 7px;
        }

        .profit-stat {
          right: 75px;
          top: 28px;
          transform: rotate(4deg);
        }

        .sales-stat {
          right: 175px;
          bottom: 42px;
          transform: rotate(-4deg);
        }

        .mini-chart {
          position: absolute;
          right: 34px;
          bottom: 34px;
          width: 150px;
          height: 70px;
          border: 1px solid #363044;
          background: rgba(18,17,27,.65);
          border-radius: 9px;
          padding: 13px;
        }

        .mini-bars {
          height: 38px;
          display: flex;
          align-items: flex-end;
          gap: 5px;
        }

        .mini-bars i {
          display: block;
          width: 10px;
          border-radius: 2px 2px 0 0;
          background:
            linear-gradient(
              180deg,
              #a855f7,
              #6336b6
            );
        }

        .mini-bars i:nth-child(1) { height: 30%; }
        .mini-bars i:nth-child(2) { height: 50%; }
        .mini-bars i:nth-child(3) { height: 42%; }
        .mini-bars i:nth-child(4) { height: 70%; }
        .mini-bars i:nth-child(5) { height: 57%; }
        .mini-bars i:nth-child(6) { height: 82%; }
        .mini-bars i:nth-child(7) { height: 68%; }

        .mini-chart span {
          position: absolute;
          bottom: 5px;
          left: 12px;
          color: #555568;
          font-size: 6px;
        }

        .ai-powered-badge {
          position: absolute;
          right: 28px;
          top: 13px;
          font-size: 6px;
          color: #666678;
          display: flex;
          align-items: center;
          gap: 5px;
        }

        .live-dot {
          width: 5px;
          height: 5px;
          border-radius: 50%;
          background: #22c55e;
          box-shadow: 0 0 7px #22c55e;
        }


        /* =========================
           KPI
        ========================= */

        .kpi-grid {
          display: grid;
          grid-template-columns:
            repeat(4, minmax(0, 1fr));
          gap: 9px;
          margin-bottom: 15px;
        }

        .kpi-card {
          position: relative;
          min-height: 128px;
          overflow: hidden;
          border: 1px solid #282934;
          border-radius: 12px;
          background: #0f1017;
          padding: 14px;
          transition: .25s ease;
        }

        .kpi-card:hover,
        .panel:hover,
        .summary-card:hover {
          transform: translateY(-2px);
          border-color: #413553;
          box-shadow:
            0 12px 35px rgba(0,0,0,.18);
        }

        .kpi-top {
          display: flex;
          justify-content: space-between;
        }

        .kpi-icon {
          width: 27px;
          height: 27px;
          border-radius: 7px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .kpi-icon.purple,
        .summary-icon.purple,
        .insight-icon.purple {
          color: #a855f7;
          background: rgba(168,85,247,.12);
        }

        .kpi-icon.green,
        .summary-icon.green,
        .insight-icon.green {
          color: #22c55e;
          background: rgba(34,197,94,.10);
        }

        .kpi-icon.blue,
        .summary-icon.blue,
        .insight-icon.blue {
          color: #3b82f6;
          background: rgba(59,130,246,.10);
        }

        .kpi-icon.orange,
        .summary-icon.orange,
        .insight-icon.orange {
          color: #f59e0b;
          background: rgba(245,158,11,.10);
        }

        .kpi-menu {
          color: #49495a;
          font-size: 8px;
        }

        .kpi-label {
          color: #666678;
          font-size: 8px;
          margin-top: 11px;
        }

        .kpi-value {
          font-size: 20px;
          font-weight: 760;
          margin-top: 4px;
          letter-spacing: -.5px;
        }

        .kpi-bottom {
          display: flex;
          align-items: center;
          gap: 5px;
          margin-top: 5px;
        }

        .positive {
          color: #22c55e;
          font-size: 7px;
          display: flex;
          align-items: center;
          gap: 2px;
        }

        .period {
          color: #49495a;
          font-size: 7px;
        }

        .sparkline {
          position: absolute;
          width: 62px;
          height: 27px;
          right: 7px;
          bottom: 9px;
        }


        /* =========================
           PANELS
        ========================= */

        .two-column {
          display: grid;
          grid-template-columns: 1.65fr 1fr;
          gap: 9px;
          margin-bottom: 15px;
        }

        .panel {
          background: #0f1017;
          border: 1px solid #282934;
          border-radius: 12px;
          transition: .25s ease;
        }

        .assistant-panel {
          padding: 17px;
          min-height: 230px;
        }

        .insights-panel {
          padding: 17px;
        }

        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
        }

        .panel-header h3 {
          margin: 0;
          font-size: 14px;
          line-height: 1.25;
          letter-spacing: -.3px;
        }

        .online {
          display: flex;
          align-items: center;
          gap: 4px;
          color: #22c55e;
          font-size: 7px;
        }

        .online span {
          width: 5px;
          height: 5px;
          background: #22c55e;
          border-radius: 50%;
        }

        .panel-description {
          color: #626274;
          font-size: 8px;
          line-height: 1.5;
          margin: 9px 0 13px;
        }

        .question-box {
          height: 72px;
          border: 1px solid #42305d;
          background: #0b0c12;
          border-radius: 9px;
          position: relative;
          display: flex;
          align-items: center;
          padding: 12px;
        }

        .question-input {
          color: #565668;
          display: flex;
          gap: 7px;
          font-size: 8px;
        }

        .question-input svg {
          color: #9b5cff;
          flex-shrink: 0;
        }

        .question-input small {
          display: inline-block;
          margin-top: 8px;
          color: #3f4050;
          font-size: 7px;
        }

        .ask-button {
          position: absolute;
          right: 8px;
          bottom: 8px;
          height: 27px;
          padding: 0 11px;
          border: 0;
          border-radius: 6px;
          color: white;
          font-size: 8px;
          font-weight: 700;
          background: linear-gradient(135deg,#7c3aed,#a855f7);
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .try-row {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          gap: 5px;
          margin-top: 10px;
        }

        .try-row > span {
          color: #4e4e5f;
          font-size: 7px;
        }

        .try-row button {
          border: 1px solid #292a38;
          color: #777789;
          background: #11121a;
          border-radius: 20px;
          padding: 5px 8px;
          font-size: 7px;
        }

        .try-row button:hover {
          color: #b98aff;
          border-color: #65449a;
        }

        .view-all {
          border: 0;
          background: transparent;
          color: #666678;
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 7px;
        }

        .insight-list {
          margin-top: 9px;
        }

        .insight-item {
          display: flex;
          gap: 9px;
          padding: 11px 0;
          border-bottom: 1px solid #1e1f29;
        }

        .insight-item:last-child {
          border-bottom: 0;
        }

        .insight-icon {
          width: 25px;
          height: 25px;
          border-radius: 7px;
          flex-shrink: 0;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .insight-content strong {
          display: block;
          font-size: 8px;
          margin-bottom: 3px;
        }

        .insight-content p {
          color: #5f6070;
          font-size: 7px;
          line-height: 1.4;
          margin: 0 0 4px;
        }

        .insight-content span {
          color: #404150;
          font-size: 6px;
        }


        /* =========================
           SALES
        ========================= */

        .sales-panel {
          padding: 18px;
          margin-bottom: 10px;
        }

        .sales-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
        }

        .sales-title-row {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .sales-title-row h2 {
          font-size: 15px;
          margin: 0;
        }

        .sales-growth {
          color: #22c55e;
          font-size: 7px;
          background: rgba(34,197,94,.08);
          padding: 4px 6px;
          border-radius: 5px;
        }

        .sales-total {
          font-size: 22px;
          font-weight: 780;
          margin-top: 5px;
        }

        .range-buttons {
          display: flex;
          gap: 3px;
          border: 1px solid #242530;
          padding: 3px;
          border-radius: 7px;
        }

        .range-buttons button {
          border: 0;
          background: transparent;
          color: #666678;
          border-radius: 5px;
          font-size: 7px;
          padding: 5px 7px;
        }

        .range-buttons button.selected {
          background: #2b1945;
          color: #bb8cff;
        }

        .chart-container {
          height: 250px;
          margin-top: 18px;
        }


        /* =========================
           SUMMARY
        ========================= */

        .summary-grid {
          display: grid;
          grid-template-columns:
            repeat(3, minmax(0, 1fr));
          gap: 9px;
        }

        .summary-card {
          min-height: 82px;
          border: 1px solid #282934;
          border-radius: 11px;
          background: #0f1017;
          padding: 13px;
          display: flex;
          align-items: flex-start;
          gap: 10px;
          transition: .25s ease;
        }

        .summary-icon {
          width: 28px;
          height: 28px;
          border-radius: 7px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }

        .summary-info {
          min-width: 0;
          flex: 1;
        }

        .summary-info > span {
          display: block;
          color: #505062;
          font-size: 6px;
          letter-spacing: 1px;
          margin-bottom: 4px;
        }

        .summary-info strong {
          display: block;
          font-size: 12px;
        }

        .summary-info p {
          color: #5e5e70;
          font-size: 7px;
          margin: 4px 0 0;
        }

        .summary-card > svg {
          color: #484858;
        }

        .confidence-bar {
          height: 3px;
          width: 100%;
          max-width: 150px;
          background: #242530;
          border-radius: 10px;
          margin-top: 7px;
        }

        .confidence-bar div {
          height: 100%;
          width: 94.8%;
          border-radius: inherit;
          background:
            linear-gradient(
              90deg,
              #7c3aed,
              #22c55e
            );
        }


        /* =========================
           RIGHT SIDEBAR
        ========================= */

        .right-sidebar {
          position: fixed;
          right: 0;
          top: 0;
          width: 285px;
          height: 100vh;
          background: #0a0b11;
          border-left: 1px solid #20212c;
          padding: 82px 18px 20px;
          overflow-y: auto;
        }

        .right-title {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          border-bottom: 1px solid #1e1f29;
          padding-bottom: 15px;
        }

        .right-title h3 {
          margin: 0;
          font-size: 15px;
        }

        .right-title button {
          width: 27px;
          height: 27px;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 1px solid #292a37;
          background: #11121a;
          color: #676778;
          border-radius: 7px;
        }

        .right-insights {
          margin-bottom: 18px;
        }

        .right-insight {
          display: flex;
          gap: 10px;
          padding: 15px 2px;
          border-bottom: 1px solid #1e1f29;
        }

        .right-dot {
          width: 7px;
          height: 7px;
          border-radius: 50%;
          flex-shrink: 0;
          margin-top: 5px;
        }

        .right-dot.purple {
          background: #a855f7;
          box-shadow: 0 0 8px rgba(168,85,247,.5);
        }

        .right-dot.green {
          background: #22c55e;
        }

        .right-dot.orange {
          background: #f59e0b;
        }

        .right-dot.blue {
          background: #3b82f6;
        }

        .right-insight strong {
          display: block;
          font-size: 9px;
          margin-bottom: 5px;
        }

        .right-insight p {
          color: #606071;
          font-size: 8px;
          line-height: 1.5;
          margin: 0 0 5px;
        }

        .right-insight span {
          color: #3f4050;
          font-size: 7px;
        }

        .advanced-card {
          position: relative;
          overflow: hidden;
          border: 1px solid #37265a;
          border-radius: 12px;
          padding: 16px;
          background:
            radial-gradient(
              circle at 80% 0%,
              rgba(124,58,237,.2),
              transparent 45%
            ),
            #13111c;
        }

        .advanced-icon {
          width: 31px;
          height: 31px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #ba83ff;
          background: rgba(124,58,237,.15);
          margin-bottom: 11px;
        }

        .advanced-card h3 {
          margin: 0 0 7px;
          font-size: 12px;
        }

        .advanced-card p {
          color: #68687a;
          font-size: 8px;
          line-height: 1.5;
          margin: 0 0 13px;
        }

        .advanced-card button {
          border: 0;
          border-radius: 7px;
          height: 30px;
          padding: 0 10px;
          color: white;
          background:
            linear-gradient(
              135deg,
              #7c3aed,
              #a855f7
            );
          font-size: 8px;
          font-weight: 700;
          display: flex;
          align-items: center;
          gap: 5px;
        }


        /* =========================
           RESPONSIVE
        ========================= */

        @media (min-width: 1500px) {

          .main-content {
            width: min(1250px, calc(100% - 70px));
          }

          .hero {
            min-height: 275px;
          }

          .hero h1 {
            font-size: 46px;
          }

        }


        @media (max-width: 1250px) {

          .right-sidebar {
            display: none;
          }

          .main-wrapper {
            width: calc(100% - 245px);
          }

          .main-content {
            width: calc(100% - 40px);
          }

        }


        @media (max-width: 850px) {

          .sidebar {
            transform: translateX(-100%);
            transition: transform .25s ease;
          }

          .sidebar.sidebar-open {
            transform: translateX(0);
          }

          .mobile-close {
            display: flex;
            margin-left: auto;
            border: 0;
            background: transparent;
            color: #777789;
          }

          .mobile-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,.65);
            z-index: 40;
          }

          .main-wrapper {
            margin-left: 0;
            width: 100%;
          }

          .hamburger {
            display: flex;
            width: 34px;
            height: 34px;
            align-items: center;
            justify-content: center;
            border: 1px solid #292a37;
            background: #101119;
            color: #aaa8ba;
            border-radius: 8px;
          }

          .navbar {
            gap: 10px;
          }

          .breadcrumb {
            display: none;
          }

          .navbar-actions {
            margin-left: auto;
          }

          .search-box {
            width: min(240px, 45vw);
          }

          .two-column {
            grid-template-columns: 1fr;
          }

          .kpi-grid {
            grid-template-columns:
              repeat(2, minmax(0, 1fr));
          }

          .summary-grid {
            grid-template-columns: 1fr;
          }

        }


        @media (max-width: 560px) {

          .main-content {
            width: calc(100% - 24px);
          }

          .navbar {
            height: 60px;
            margin-bottom: 15px;
          }

          .search-box {
            display: none;
          }

          .hero {
            min-height: 390px;
          }

          .hero-content {
            padding: 27px 22px;
          }

          .hero h1 {
            font-size: 31px;
          }

          .hero p {
            max-width: 100%;
          }

          .profit-stat {
            top: auto;
            right: 20px;
            bottom: 105px;
          }

          .sales-stat {
            right: 140px;
            bottom: 70px;
          }

          .mini-chart {
            right: 20px;
            bottom: 20px;
            width: 135px;
          }

          .ai-powered-badge {
            display: none;
          }

          .kpi-grid {
            grid-template-columns: 1fr;
          }

          .kpi-card {
            min-height: 115px;
          }

          .chart-container {
            height: 220px;
          }

          .sales-header {
            gap: 10px;
          }

          .range-buttons {
            flex-shrink: 0;
          }

          .sales-total {
            font-size: 19px;
          }

          .sales-title-row h2 {
            font-size: 13px;
          }

        }

      `}</style>


      <div className="metricmind-app">

        <Sidebar
          mobileOpen={mobileOpen}
          setMobileOpen={setMobileOpen}
        />


        <div className="main-wrapper">

          <main className="main-content">

            <Navbar
              setMobileOpen={setMobileOpen}
            />


            <HeroBanner />


            <section className="kpi-grid">

              <KpiCard
                icon={Wallet}
                label="Total Revenue"
                value="₹56,591"
                change="+12.4%"
                color="purple"
                data={sparkRevenue}
              />

              <KpiCard
                icon={TrendingUp}
                label="Total Profit"
                value="₹24,813"
                change="+8.7%"
                color="green"
                data={sparkProfit}
              />

              <KpiCard
                icon={ShoppingCart}
                label="Total Orders"
                value="1,999"
                change="+4.2%"
                color="blue"
                data={sparkOrders}
              />

              <KpiCard
                icon={Target}
                label="Avg. Order Value"
                value="₹28.31"
                change="+4.7%"
                color="orange"
                data={sparkAov}
              />

            </section>


            <section className="two-column">

              <AiAssistant />

              <InsightsPanel />

            </section>


            <SalesPerformance />


            <SummaryCards />

          </main>

        </div>


        <RightSidebar />

      </div>
    </>
  );
}

export default Dashboard;