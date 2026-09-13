import {
  Bell,
  Command,
  Moon,
  Search,
} from "lucide-react";

function Navbar() {
  return (
    <header className="top-navbar">
      <div className="search-box">
        <Search size={16} />

        <input
          type="text"
          placeholder="Search anything... (e.g. sales, profit, region...)"
        />

        <span className="shortcut">
          <Command size={11} />
          K
        </span>
      </div>

      <div className="navbar-actions">
        <button className="icon-button">
          <Moon size={17} />
        </button>

        <button className="icon-button notification">
          <Bell size={17} />
          <span />
        </button>

        <div className="navbar-avatar">MY</div>
      </div>
    </header>
  );
}

export default Navbar;