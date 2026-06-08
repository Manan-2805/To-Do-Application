import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { CheckSquare, LayoutDashboard, ListTodo, ClipboardList, LogOut } from "lucide-react";

import ThemeToggle from "./ThemeToggle";
import { logout } from "../api/auth";

interface HeaderProps {
  username?: string;
  onLogout: () => void;
}

export const Header: React.FC<HeaderProps> = ({ username, onLogout }) => {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
    } catch {
      // Fail silently
    }
    onLogout();
    navigate("/login");
  };

  return (
    <header className="app-header fade-in">
      <div className="brand" onClick={() => navigate("/dashboard")} style={{ cursor: "pointer" }}>
        <CheckSquare size={28} style={{ color: "var(--accent-color)" }} />
        <span>TodoSphere</span>
      </div>

      <nav style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
        <NavLink
          to="/dashboard"
          className={({ isActive }) => `btn ${isActive ? "btn-primary" : "btn-secondary"}`}
          style={{ padding: "0.5rem 1rem", fontSize: "0.875rem" }}
        >
          <LayoutDashboard size={16} />
          <span style={{ marginLeft: "0.25rem" }}>Dashboard</span>
        </NavLink>

        <NavLink
          to="/tasks"
          className={({ isActive }) => `btn ${isActive ? "btn-primary" : "btn-secondary"}`}
          style={{ padding: "0.5rem 1rem", fontSize: "0.875rem" }}
        >
          <ListTodo size={16} />
          <span style={{ marginLeft: "0.25rem" }}>Tasks</span>
        </NavLink>

        <NavLink
          to="/audit"
          className={({ isActive }) => `btn ${isActive ? "btn-primary" : "btn-secondary"}`}
          style={{ padding: "0.5rem 1rem", fontSize: "0.875rem" }}
        >
          <ClipboardList size={16} />
          <span style={{ marginLeft: "0.25rem" }}>Audits</span>
        </NavLink>
      </nav>

      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        {username && (
          <span style={{ fontSize: "0.875rem", fontWeight: 500, color: "var(--text-secondary)" }}>
            Hi, <strong>{username}</strong>
          </span>
        )}
        <ThemeToggle />
        <button
          onClick={handleLogout}
          className="btn btn-secondary"
          style={{ padding: "0.5rem 1rem", fontSize: "0.875rem", display: "flex", alignItems: "center", gap: "0.25rem" }}
          aria-label="Logout"
        >
          <LogOut size={16} />
          <span>Logout</span>
        </button>
      </div>
    </header>
  );
};

export default Header;
