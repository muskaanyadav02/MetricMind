
import { useEffect, useState } from "react";
import {
  Bell,
  Database,
  Moon,
  Shield,
  User,
  Sun,
  CheckCircle,
  RefreshCw,
} from "lucide-react";

import "./Settings.css";

function Settings() {
  const [activeTab, setActiveTab] = useState("Profile");

  const [name, setName] = useState("Muskaan Yadav");
  const [role, setRole] = useState("AI Agent Engineer");

  const [emailAlerts, setEmailAlerts] = useState(true);
  const [insightAlerts, setInsightAlerts] = useState(true);
  const [reportAlerts, setReportAlerts] = useState(false);
  const [confirmExport, setConfirmExport] = useState(true);

  const [theme, setTheme] = useState(() => {
    const savedTheme = localStorage.getItem("metricmind-theme");
    return savedTheme === "Light mode" ? "Light mode" : "Dark mode";
  });

  const [notice, setNotice] = useState("");

  const tabs = [
    { label: "Profile", icon: User },
    { label: "Data Sources", icon: Database },
    { label: "Notifications", icon: Bell },
    { label: "Security", icon: Shield },
    { label: "Appearance", icon: Moon },
  ];

  // Apply the selected theme globally and remember it in this browser.
  useEffect(() => {
    document.documentElement.dataset.theme =
      theme === "Light mode" ? "light" : "dark";

    localStorage.setItem("metricmind-theme", theme);
  }, [theme]);

  function changeTab(tab) {
    setActiveTab(tab);
    setNotice("");
  }

  function saveSettings() {
    setNotice("Changes saved for this session.");
  }

  return (
    <div className="settings-page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">SETTINGS</span>
          <h1>Settings</h1>
          <p>Manage your MetricMind workspace and preferences.</p>
        </div>
      </div>

      <div className="settings-layout">
        {/* Settings navigation */}
        <div className="settings-menu">
          {tabs.map((tab) => {
            const TabIcon = tab.icon;

            return (
              <button
                key={tab.label}
                type="button"
                className={activeTab === tab.label ? "active" : ""}
                onClick={() => changeTab(tab.label)}
              >
                <TabIcon size={16} />
                {tab.label}
              </button>
            );
          })}
        </div>

        <div className="settings-card">
          {/* PROFILE */}
          {activeTab === "Profile" && (
            <>
              <div className="settings-section">
                <span className="eyebrow">PROFILE</span>
                <h3>Personal information</h3>
                <p>
                  Update the information associated with your MetricMind
                  account.
                </p>
              </div>

              <div className="form-grid">
                <label>
                  <span>Full name</span>
                  <input
                    value={name}
                    onChange={(event) => setName(event.target.value)}
                    placeholder="Enter your name"
                  />
                </label>

                <label>
                  <span>Role</span>
                  <input
                    value={role}
                    onChange={(event) => setRole(event.target.value)}
                    placeholder="Enter your role"
                  />
                </label>

                <label>
                  <span>Workspace</span>
                  <input value="Global Superstore" readOnly />
                </label>

                <label>
                  <span>Current theme</span>
                  <div className="theme-option">
                    {theme === "Light mode" ? (
                      <Sun size={15} />
                    ) : (
                      <Moon size={15} />
                    )}
                    {theme}
                  </div>
                </label>
              </div>

              <button
                type="button"
                className="primary-button save-button"
                onClick={saveSettings}
              >
                Save Changes
              </button>
            </>
          )}

          {/* DATA SOURCES */}
          {activeTab === "Data Sources" && (
            <>
              <div className="settings-section">
                <span className="eyebrow">DATA SOURCES</span>
                <h3>Connected data</h3>
                <p>View the data source configured for your workspace.</p>
              </div>

              <div className="settings-info-card">
                <Database size={22} />

                <div>
                  <h3>Global Superstore</h3>
                  <p>
                    Business sales, profit, product, and regional data.
                  </p>

                  <span className="settings-status">
                    <span className="status-dot" />
                    Workspace data source
                  </span>
                </div>
              </div>

              <button
                type="button"
                className="primary-button save-button"
                onClick={() =>
                  setNotice(
                    "This panel displays the configured workspace data source."
                  )
                }
              >
                <RefreshCw size={15} />
                Check Configuration
              </button>
            </>
          )}

          {/* NOTIFICATIONS */}
          {activeTab === "Notifications" && (
            <>
              <div className="settings-section">
                <span className="eyebrow">NOTIFICATIONS</span>
                <h3>Notification preferences</h3>
                <p>Choose which notification preferences to enable.</p>
              </div>

              <div className="settings-options">
                <label className="settings-toggle">
                  <span>
                    <strong>Email notifications</strong>
                    <small>General workspace updates</small>
                  </span>

                  <input
                    type="checkbox"
                    checked={emailAlerts}
                    onChange={(event) =>
                      setEmailAlerts(event.target.checked)
                    }
                  />
                </label>

                <label className="settings-toggle">
                  <span>
                    <strong>Business insight alerts</strong>
                    <small>Updates about business findings</small>
                  </span>

                  <input
                    type="checkbox"
                    checked={insightAlerts}
                    onChange={(event) =>
                      setInsightAlerts(event.target.checked)
                    }
                  />
                </label>

                <label className="settings-toggle">
                  <span>
                    <strong>Report notifications</strong>
                    <small>Updates related to reports</small>
                  </span>

                  <input
                    type="checkbox"
                    checked={reportAlerts}
                    onChange={(event) =>
                      setReportAlerts(event.target.checked)
                    }
                  />
                </label>
              </div>

              <button
                type="button"
                className="primary-button save-button"
                onClick={saveSettings}
              >
                Save Preferences
              </button>
            </>
          )}

          {/* SECURITY */}
          {activeTab === "Security" && (
            <>
              <div className="settings-section">
                <span className="eyebrow">SECURITY</span>
                <h3>Security preferences</h3>
                <p>Manage your report export confirmation preference.</p>
              </div>

              <div className="settings-options">
                <label className="settings-toggle">
                  <span>
                    <strong>Confirm before exporting</strong>
                    <small>
                      Enable an additional confirmation preference for exports.
                    </small>
                  </span>

                  <input
                    type="checkbox"
                    checked={confirmExport}
                    onChange={(event) =>
                      setConfirmExport(event.target.checked)
                    }
                  />
                </label>
              </div>

              <p className="settings-note">
                Password changes, authentication, and account security
                require backend integration and are not implemented here.
              </p>

              <button
                type="button"
                className="primary-button save-button"
                onClick={saveSettings}
              >
                Save Preferences
              </button>
            </>
          )}

          {/* APPEARANCE */}
          {activeTab === "Appearance" && (
            <>
              <div className="settings-section">
                <span className="eyebrow">APPEARANCE</span>
                <h3>Display preferences</h3>
                <p>Select your preferred application theme.</p>
              </div>

              <div className="settings-options">
                <button
                  type="button"
                  className={`appearance-choice ${
                    theme === "Dark mode" ? "selected" : ""
                  }`}
                  onClick={() => {
                    setTheme("Dark mode");
                    setNotice("Dark mode is now active.");
                  }}
                >
                  <Moon size={18} />
                  <span>Dark mode</span>
                  {theme === "Dark mode" && <CheckCircle size={17} />}
                </button>

                <button
                  type="button"
                  className={`appearance-choice ${
                    theme === "Light mode" ? "selected" : ""
                  }`}
                  onClick={() => {
                    setTheme("Light mode");
                    setNotice("Light mode is now active.");
                  }}
                >
                  <Sun size={18} />
                  <span>Light mode</span>
                  {theme === "Light mode" && <CheckCircle size={17} />}
                </button>
              </div>

              <p className="settings-note">
                Your selected theme is saved in this browser and applied
                through the application's global theme variables.
              </p>
            </>
          )}

          {notice && (
            <p className="settings-notice" role="status">
              {notice}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default Settings;
