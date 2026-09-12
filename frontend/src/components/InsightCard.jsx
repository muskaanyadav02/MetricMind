import {
  Sparkles,
  TrendingUp,
  AlertTriangle,
} from 'lucide-react'

export default function InsightCard({
  title,
  description,
  timestamp,
  type = 'purple',
}) {
  const styles = {
    purple: 'bg-violet-500/15 text-violet-300',
    green: 'bg-emerald-500/15 text-emerald-300',
    amber: 'bg-amber-500/15 text-amber-300',
    blue: 'bg-blue-500/15 text-blue-300',
  }

  const Icon =
    type === 'green'
      ? TrendingUp
      : type === 'amber'
        ? AlertTriangle
        : Sparkles

  return (
    <div className="
      flex gap-3 border-b border-[#22222d]
      py-4 last:border-0
    ">
      <div className={`
        flex h-8 w-8 shrink-0
        items-center justify-center
        rounded-lg ${styles[type]}
      `}>
        <Icon size={14} />
      </div>

      <div className="min-w-0">
        <h4 className="text-[11px] font-semibold text-white">
          {title}
        </h4>

        <p className="
          mt-1 text-[9px]
          leading-4 text-gray-500
        ">
          {description}
        </p>

        <p className="
          mt-1 text-[8px] text-gray-700
        ">
          {timestamp}
        </p>
      </div>
    </div>
  )
}