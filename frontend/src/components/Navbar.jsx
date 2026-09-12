import {
  Search,
  Bell,
  Moon,
  Menu,
} from 'lucide-react'

export default function Navbar({ onMenuClick }) {
  return (
    <header className="
      sticky top-0 z-30
      flex h-[68px] items-center
      border-b border-[#1f1f29]
      bg-[#08080d]/90
      px-4 backdrop-blur-xl
      lg:px-7
    ">
      <button
        onClick={onMenuClick}
        className="mr-4 text-gray-400 lg:hidden"
      >
        <Menu size={21} />
      </button>

      <div className="
        flex w-full items-center justify-between gap-4
      ">
        <div className="
          hidden h-9 w-full max-w-[430px]
          items-center gap-2
          rounded-xl border border-[#292936]
          bg-[#111119] px-3
          md:flex
        ">
          <Search size={14} className="text-gray-500" />

          <input
            className="
              w-full bg-transparent
              text-xs text-white outline-none
              placeholder:text-gray-600
            "
            placeholder="Search anything... (e.g. sales, profit, region...)"
          />

          <span className="
            rounded-md border border-[#30303b]
            px-1.5 py-0.5
            text-[9px] text-gray-600
          ">
            ⌘K
          </span>
        </div>

        <div className="ml-auto flex items-center gap-2">

          <button className="
            flex h-9 w-9 items-center justify-center
            rounded-xl border border-[#292936]
            bg-[#111119]
            text-gray-400
            transition hover:border-violet-500/40
            hover:text-white
          ">
            <Moon size={15} />
          </button>

          <button className="
            relative flex h-9 w-9 items-center justify-center
            rounded-xl border border-[#292936]
            bg-[#111119]
            text-gray-400
          ">
            <Bell size={15} />

            <span className="
              absolute right-2 top-2
              h-1.5 w-1.5 rounded-full
              bg-red-500
            " />
          </button>

          <div className="
            flex h-9 w-9 items-center justify-center
            rounded-xl
            bg-gradient-to-br from-violet-500 to-indigo-600
            text-[9px] font-bold text-white
          ">
            MY
          </div>

        </div>
      </div>
    </header>
  )
}