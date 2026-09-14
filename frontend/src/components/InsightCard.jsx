import {
  AlertTriangle,
  ArrowUpRight,
  BarChart3,
  Sparkles,
} from "lucide-react";

function InsightCard({
  title,
  description,
  time,
  type = "purple",
}) {
  const icons = {
    purple: Sparkles,
    blue: BarChart3,
    orange: AlertTriangle,
    green: ArrowUpRight,
  };

  const Icon = icons[type] || Sparkles;

  return (
    <div className="insight-card">
      <div className={`insight-icon ${type}`}>
        <Icon size={16} />
      </div>

      <div className="insight-content">
        <strong>{title}</strong>
        <p>{description}</p>
        <small>AI analysis • {time}</small>
      </div>
    </div>
  );
}

export default InsightCard;