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

function ChartCard({
  title,
  subtitle,
  data,
  dataKey,
  xKey,
  type = "area",
}) {
  return (
    <div className="chart-card">
      <div className="chart-header">
        <div>
          <h3>{title}</h3>
          {subtitle && <p>{subtitle}</p>}
        </div>

        <button className="chart-menu">•••</button>
      </div>

      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height="100%">
          {type === "bar" ? (
            <BarChart data={data}>
              <CartesianGrid
                stroke="rgba(255,255,255,0.06)"
                vertical={false}
              />

              <XAxis
                dataKey={xKey}
                axisLine={false}
                tickLine={false}
                tick={{
                  fill: "#6f7182",
                  fontSize: 11,
                }}
              />

              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{
                  fill: "#6f7182",
                  fontSize: 11,
                }}
              />

              <Tooltip
                contentStyle={{
                  background: "#151622",
                  border: "1px solid rgba(255,255,255,.1)",
                  borderRadius: "10px",
                  color: "#fff",
                }}
              />

              <Bar
                dataKey={dataKey}
                fill="#8b5cf6"
                radius={[5, 5, 0, 0]}
              />
            </BarChart>
          ) : (
            <AreaChart data={data}>
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
                axisLine={false}
                tickLine={false}
                tick={{
                  fill: "#6f7182",
                  fontSize: 11,
                }}
              />

              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{
                  fill: "#6f7182",
                  fontSize: 11,
                }}
              />

              <Tooltip
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
                strokeWidth={3}
                fill="url(#salesGradient)"
              />
            </AreaChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default ChartCard;