import {
  BarChart3,
  Bot,
  ChevronDown,
  FileText,
  Gauge,
  Lightbulb,
  Settings,
  Sparkles,
} from "lucide-react";

import { NavLink } from "react-router-dom";

function Sidebar() {
  const navigation = [
    {
      label: "Dashboard",
      path: "/dashboard",
      icon: Gauge,
    },
    {
      label: "Ask MetricMind",
      path: "/ask",
      icon: Bot,
      badge: "AI",
    },
    {
      label: "Analytics",
      path: "/analytics",
      icon: BarChart3,
    },
    {
      label: "Insights",
      path: "/insights",
      icon: Lightbulb,
    },
    {
      label: "Reports",
      path: "/reports",
      icon: FileText,
    },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">
          <Sparkles size={18} />
        </div>

        <div>
          <div className="brand-name">MetricMind</div>
          <div className="brand-subtitle">AI BUSINESS INTELLIGENCE</div>
        </div>
      </div>

      <div className="workspace-label">WORKSPACE</div>

      <button className="workspace-selector">
        <span className="online-dot" />
        <span>Global Superstore</span>
        <ChevronDown size={15} />
      </button>

      <div className="nav-label">MAIN MENU</div>

      <nav className="sidebar-nav">
        {navigation.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `nav-item ${isActive ? "active" : ""}`
              }
            >
              <Icon size={17} strokeWidth={1.8} />

              <span>{item.label}</span>

              {item.badge && (
                <span className="nav-badge">{item.badge}</span>
              )}
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-spacer" />

      <div className="upgrade-card">
        <div className="upgrade-icon">
          <Sparkles size={18} />
        </div>

        <h3>Smarter Insights.</h3>
        <h3>Bigger Decisions.</h3>

        <p>
          Unlock deeper analysis and advanced AI insights.
        </p>

        <button>Upgrade to Pro</button>
      </div>

      <NavLink
        to="/settings"
        className={({ isActive }) =>
          `settings-link ${isActive ? "active" : ""}`
        }
      >
        <Settings size={16} />
        <span>Settings</span>
      </NavLink>

      <div className="user-profile">
        <div className="avatar">MY</div>

        <div className="user-info">
          <strong>Muskaan Yadav</strong>
          <span>AI Agent Engineer</span>
        </div>

        <span className="user-menu">•••</span>
      </div>
    </aside>
  );
}

export default Sidebar;