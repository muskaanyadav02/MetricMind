import { Outlet } from "react-router-dom";

import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";

import "./DashboardLayout.css";

function DashboardLayout() {
  return (
    <div className="app-shell">
      <Sidebar />

      <div className="app-main">
        <Navbar />

        <main className="page-container">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default DashboardLayout;