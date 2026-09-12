import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import Navbar from '../components/Navbar'

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-[#08080d] text-white">

      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="lg:pl-[250px]">

        <Navbar
          onMenuClick={() => setSidebarOpen(true)}
        />

        <main className="
          min-h-[calc(100vh-68px)]
          p-4 sm:p-5 lg:p-7
        ">
          <Outlet />
        </main>

      </div>
    </div>
  )
}