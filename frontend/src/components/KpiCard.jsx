import {
  ArrowDownRight,
  ArrowUpRight,
} from "lucide-react";

function KpiCard({
  title,
  value,
  change,
  icon: Icon,
  type = "purple",
}) {
  const positive = !String(change).includes("-");

  return (
    <div className="kpi-card">
      <div className={`kpi-icon ${type}`}>
        <Icon size={18} />
      </div>

      <div className="kpi-content">
        <span className="kpi-title">{title}</span>

        <strong className="kpi-value">{value}</strong>

        <div className="kpi-bottom">
          <span
            className={`kpi-change ${
              positive ? "positive" : "negative"
            }`}
          >
            {positive ? (
              <ArrowUpRight size={13} />
            ) : (
              <ArrowDownRight size={13} />
            )}

            {change}
          </span>

          <span className="kpi-period">vs last period</span>
        </div>
      </div>

      <div className={`mini-sparkline ${type}`}>
        <span />
        <span />
        <span />
        <span />
        <span />
        <span />
      </div>
    </div>
  );
}

export default KpiCard;