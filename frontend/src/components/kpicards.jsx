import {
  TrendingUp,
  ArrowUpRight,
} from 'lucide-react'
import {
  LineChart,
  Line,
  ResponsiveContainer,
} from 'recharts'

export default function KpiCard({
  title,
  value,
  change,
  icon: Icon,
  iconClass,
  data = [],
}) {
  return (
    <div className="
      group relative overflow-hidden
      rounded-2xl border border-[#252532]
      bg-[#101016]
      p-4
      transition-all duration-300
      hover:-translate-y-1
      hover:border-violet-500/30
      hover:shadow-xl hover:shadow-violet-950/10
    ">

      <div className="flex items-start justify-between">

        <div>
          <div className="flex items-center gap-2">
            <div className={`
              flex h-8 w-8 items-center justify-center
              rounded-lg ${iconClass}
            `}>
              <Icon size={15} />
            </div>

            <span className="text-[10px] text-gray-500">
              {title}
            </span>
          </div>

          <h3 className="
            mt-3 text-xl font-bold
            tracking-tight text-white
          ">
            {value}
          </h3>

          <div className="
            mt-1 flex items-center gap-1
            text-[9px] text-emerald-400
          ">
            <TrendingUp size={10} />
            {change}
            <span className="text-gray-600">
              vs last period
            </span>
          </div>
        </div>

        <ArrowUpRight
          size={14}
          className="
            text-gray-700
            transition group-hover:text-violet-400
          "
        />

      </div>

      {data.length > 1 && (
        <div className="
          pointer-events-none absolute
          bottom-2 right-2 h-12 w-24
          opacity-70
        ">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <Line
                type="monotone"
                dataKey="value"
                stroke="#8b5cf6"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}