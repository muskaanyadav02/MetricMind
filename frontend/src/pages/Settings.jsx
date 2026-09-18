import {
  Bell,
  Database,
  Moon,
  Shield,
  User,
} from "lucide-react";

import "./Settings.css";

function Settings() {
  return (
    <div className="settings-page">

      <div className="page-heading">
        <div>
          <span className="eyebrow">SETTINGS</span>
          <h1>Settings</h1>
          <p>
            Manage your MetricMind workspace and preferences.
          </p>
        </div>
      </div>

      <div className="settings-layout">

        <div className="settings-menu">
          <button className="active">
            <User size={16} />
            Profile
          </button>

          <button>
            <Database size={16} />
            Data Sources
          </button>

          <button>
            <Bell size={16} />
            Notifications
          </button>

          <button>
            <Shield size={16} />
            Security
          </button>

          <button>
            <Moon size={16} />
            Appearance
          </button>
        </div>

        <div className="settings-card">

          <div className="settings-section">
            <span className="eyebrow">PROFILE</span>
            <h3>Personal information</h3>
            <p>
              Update the information associated with your MetricMind account.
            </p>
          </div>

          <div className="form-grid">

            <label>
              <span>Full name</span>
              <input value="Muskaan Yadav" readOnly />
            </label>

            <label>
              <span>Role</span>
              <input value="AI Agent Engineer" readOnly />
            </label>

            <label>
              <span>Workspace</span>
              <input value="Global Superstore" readOnly />
            </label>

            <label>
              <span>Theme</span>

              <div className="theme-option">
                <Moon size={15} />
                Dark mode
              </div>
            </label>

          </div>

          <button className="primary-button save-button">
            Save Changes
          </button>

        </div>
      </div>
    </div>
  );
}

export default Settings;