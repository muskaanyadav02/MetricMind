import { useState } from 'react'
import {
  LayoutDashboard,
  Sparkles,
  BarChart3,
  Lightbulb,
  FileText,
  Settings,
  ChevronDown,
  Brain,
  X,
  Zap,
} from 'lucide-react'
import { NavLink } from 'react-router-dom'

const navigation = [
  {
    name: 'Dashboard',
    path: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    name: 'Ask MetricMind',
    path: '/ask',
    icon: Sparkles,
    badge: 'AI',
  },
  {
    name: 'Analytics',
    path: '/analytics',
    icon: BarChart3,
  },
  {
    name: 'Insights',
    path: '/insights',
    icon: Lightbulb,
  },
  {
    name: 'Reports',
    path: '/reports',
    icon: FileText,
  },
]

export default function Sidebar({ open, onClose }) {
  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/70 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`
          fixed left-0 top-0 z-50 h-screen w-[250px]
          border-r border-[#252532]
          bg-[#0a0a10]
          transition-transform duration-300
          lg:translate-x-0
          ${open ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        <div className="flex h-full flex-col p-4">

          <div className="mb-8 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="
                flex h-10 w-10 items-center justify-center
                rounded-xl
                bg-gradient-to-br from-violet-500 to-indigo-600
                shadow-lg shadow-violet-500/25
              ">
                <Brain size={20} />
              </div>

              <div>
                <h1 className="text-sm font-bold text-white">
                  MetricMind
                </h1>

                <p className="text-[9px] tracking-[0.18em] text-gray-500">
                  AI BUSINESS INTELLIGENCE
                </p>
              </div>
            </div>

            <button
              onClick={onClose}
              className="text-gray-500 lg:hidden"
            >
              <X size={19} />
            </button>
          </div>

          <p className="
            mb-2 px-2
            text-[9px] font-semibold uppercase
            tracking-[0.2em] text-gray-600
          ">
            Workspace
          </p>

          <button className="
            mb-7 flex w-full items-center justify-between
            rounded-xl border border-[#292936]
            bg-[#12121a] px-3 py-3
            text-xs
            transition hover:border-violet-500/40
          ">
            <span className="flex items-center gap-2">
              <span className="
                h-2 w-2 rounded-full bg-emerald-400
                shadow-[0_0_8px_rgba(52,211,153,.8)]
              " />
              Global Superstore
            </span>

            <ChevronDown size={14} className="text-gray-500" />
          </button>

          <p className="
            mb-2 px-2
            text-[9px] font-semibold uppercase
            tracking-[0.2em] text-gray-600
          ">
            Main Menu
          </p>

          <nav className="space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon

              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={onClose}
                  className={({ isActive }) => `
                    group flex items-center justify-between
                    rounded-xl px-3 py-3 text-xs
                    transition-all duration-200
                    ${
                      isActive
                        ? `
                          bg-gradient-to-r
                          from-violet-600/25
                          to-violet-500/5
                          text-white
                          shadow-[inset_2px_0_0_#8b5cf6]
                        `
                        : `
                          text-gray-500
                          hover:bg-white/[0.03]
                          hover:text-gray-200
                        `
                    }
                  `}
                >
                  <span className="flex items-center gap-3">
                    <Icon size={15} />

                    {item.name}
                  </span>

                  {item.badge && (
                    <span className="
                      rounded-md bg-violet-500/20
                      px-1.5 py-0.5
                      text-[8px] font-bold text-violet-300
                    ">
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              )
            })}
          </nav>

          <div className="mt-auto">

            <div className="
              relative overflow-hidden
              rounded-2xl border border-violet-500/25
              bg-gradient-to-br
              from-violet-950/70
              via-[#171126]
              to-[#0e0d17]
              p-4
            ">
              <div className="
                absolute -right-8 -top-8
                h-24 w-24 rounded-full
                bg-violet-500/15 blur-2xl
              " />

              <div className="
                mb-3 flex h-8 w-8 items-center justify-center
                rounded-lg bg-violet-500/20
                text-violet-300
              ">
                <Zap size={16} />
              </div>

              <h3 className="text-xs font-semibold text-white">
                Smarter Insights.
                <br />
                Bigger Decisions.
              </h3>

              <p className="mt-2 text-[9px] leading-4 text-gray-500">
                Unlock deeper analysis and advanced AI insights.
              </p>

              <button className="
                mt-4 flex w-full items-center justify-center
                rounded-lg
                bg-gradient-to-r from-violet-600 to-purple-500
                py-2 text-[9px] font-semibold
                text-white
                shadow-lg shadow-violet-600/20
                transition hover:scale-[1.02]
              ">
                Upgrade to Pro
              </button>
            </div>

            <button className="
              mt-5 flex w-full items-center gap-3
              px-2 text-xs text-gray-500
              hover:text-white
            ">
              <Settings size={14} />
              Settings
            </button>

            <div className="
              mt-4 border-t border-[#20202b]
              pt-4
              flex items-center gap-3
            ">
              <div className="
                flex h-8 w-8 items-center justify-center
                rounded-full
                bg-gradient-to-br from-violet-500 to-purple-700
                text-[10px] font-bold
              ">
                MY
              </div>

              <div className="min-w-0">
                <p className="truncate text-[10px] font-semibold text-white">
                  Muskaan Yadav
                </p>

                <p className="text-[8px] text-gray-600">
                  AI Agent Engineer
                </p>
              </div>
            </div>

          </div>
        </div>
      </aside>
    </>
  )
}