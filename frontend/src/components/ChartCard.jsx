
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Bar,
  BarChart,
} from "recharts";

function formatAxisLabel(value) {
  if (value == null) return "";

  const text = String(value);

  // Format ISO dates and date-like strings as Jan '11.
  if (/^\d{4}-\d{2}-\d{2}/.test(text)) {
    const date = new Date(text);

    if (!Number.isNaN(date.getTime())) {
      return date.toLocaleDateString("en-US", {
        month: "short",
        year: "2-digit",
        timeZone: "UTC",
      });
    }
  }

  return text;
}

function formatNumber(value) {
  const number = Number(value);

  if (!Number.isFinite(number)) return value;

  return new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 2,
  }).format(number);
}

function ChartCard({
  title,
  subtitle,
  data,
  dataKey,
  xKey,
  type = "area",
}) {
  const isBar = type === "bar";

  return (
    <div className="chart-card">
      <div className="chart-header">
        <div>
          <h3>{title}</h3>
          {subtitle && <p>{subtitle}</p>}
        </div>
      </div>

      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height="100%">
          {isBar ? (
            <BarChart
              data={data}
              margin={{ top: 8, right: 12, left: 0, bottom: 8 }}
              barCategoryGap="25%"
            >
              <CartesianGrid
                stroke="rgba(255,255,255,0.06)"
                vertical={false}
              />

              <XAxis
                dataKey={xKey}
                tickFormatter={formatAxisLabel}
                interval="preserveStartEnd"
                minTickGap={20}
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#85879b", fontSize: 11 }}
              />

              <YAxis
                width={58}
                tickFormatter={formatNumber}
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#85879b", fontSize: 11 }}
              />

              <Tooltip
                cursor={false}
                formatter={(value) => formatNumber(value)}
                labelFormatter={(label) => formatAxisLabel(label)}
                contentStyle={{
                  background: "#151622",
                  border: "1px solid rgba(255,255,255,.1)",
                  borderRadius: "10px",
                  color: "#fff",
                }}
              />

              <Bar
                dataKey={dataKey}
                name={dataKey}
                fill="#8b5cf6"
                radius={[5, 5, 0, 0]}
                activeBar={{ fill: "#a78bfa" }}
              />
            </BarChart>
          ) : (
            <AreaChart
              data={data}
              margin={{ top: 8, right: 12, left: 0, bottom: 8 }}
            >
              <defs>
                <linearGradient
                  id="metricMindSalesGradient"
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                >
                  <stop
                    offset="0%"
                    stopColor="#8b5cf6"
                    stopOpacity={0.35}
                  />
                  <stop
                    offset="100%"
                    stopColor="#8b5cf6"
                    stopOpacity={0}
                  />
                </linearGradient>
              </defs>

              <CartesianGrid
                stroke="rgba(255,255,255,0.06)"
                vertical={false}
              />

              <XAxis
                dataKey={xKey}
                tickFormatter={formatAxisLabel}
                interval="preserveStartEnd"
                minTickGap={28}
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#85879b", fontSize: 11 }}
              />

              <YAxis
                width={58}
                tickFormatter={formatNumber}
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#85879b", fontSize: 11 }}
              />

              <Tooltip
                formatter={(value) => formatNumber(value)}
                labelFormatter={(label) => formatAxisLabel(label)}
                contentStyle={{
                  background: "#151622",
                  border: "1px solid rgba(255,255,255,.1)",
                  borderRadius: "10px",
                  color: "#fff",
                }}
              />

              <Area
                type="monotone"
                dataKey={dataKey}
                stroke="#a78bfa"
                strokeWidth={2.5}
                fill="url(#metricMindSalesGradient)"
                dot={false}
                activeDot={{ r: 4 }}
              />
            </AreaChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default ChartCard;