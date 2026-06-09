import React, { useEffect, useState } from "react";

import { BarChart3, CheckCircle2, ClipboardList, Hourglass, PlayCircle } from "lucide-react";

import { getStats } from "../api/tasks";
import type { DashboardStats } from "../api/tasks";
import TaskChart from "../components/TaskChart";

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getStats();
        setStats(data);
      } catch (err: unknown) {
        const errorMsg =
          err instanceof Error ? err.message : "Failed to load dashboard statistics.";
        setError(errorMsg);
      } finally {
        setLoading(false);
      }
    };

    // react-doctor-disable-next-line react-doctor/no-initialize-state
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div style={{ display: "flex", flex: 1, alignItems: "center", justifyContent: "center" }}>
        <p style={{ color: "var(--text-secondary)" }}>Loading dashboard stats...</p>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div
        style={{
          display: "flex",
          flex: 1,
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column",
        }}
      >
        <p style={{ color: "var(--danger-color)", marginBottom: "1rem" }}>
          {error || "Error loading dashboard."}
        </p>
      </div>
    );
  }

  const pendingCount = stats.counts["Pending"] || 0;
  const progressCount = stats.counts["In Progress"] || 0;
  const doneCount = stats.counts["Done"] || 0;
  const missedCount = stats.counts["Missed"] || 0;

  return (
    <div className="fade-in" style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
      <div>
        <h2 style={{ fontSize: "1.75rem", marginBottom: "0.25rem", color: "var(--text-primary)" }}>
          Dashboard Metrics
        </h2>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
          Real-time metrics on task distribution and progress tracking.
        </p>
      </div>

      {/* Summary Cards Grid */}
      <div className="dashboard-grid">
        <div className="card stats-card">
          <div>
            <span
              style={{
                fontSize: "0.85rem",
                fontWeight: 600,
                color: "var(--text-secondary)",
                textTransform: "uppercase",
              }}
            >
              Total Tasks
            </span>
            <div className="stats-value">{stats.total}</div>
          </div>
          <div
            style={{
              padding: "0.75rem",
              borderRadius: "12px",
              backgroundColor: "rgba(99, 102, 241, 0.1)",
              color: "var(--accent-color)",
            }}
          >
            <BarChart3 size={24} />
          </div>
        </div>

        <div className="card stats-card">
          <div>
            <span
              style={{
                fontSize: "0.85rem",
                fontWeight: 600,
                color: "var(--text-secondary)",
                textTransform: "uppercase",
              }}
            >
              Done
            </span>
            <div className="stats-value" style={{ color: "var(--success-color)" }}>
              {doneCount}
            </div>
          </div>
          <div
            style={{
              padding: "0.75rem",
              borderRadius: "12px",
              backgroundColor: "rgba(16, 185, 129, 0.1)",
              color: "var(--success-color)",
            }}
          >
            <CheckCircle2 size={24} />
          </div>
        </div>

        <div className="card stats-card">
          <div>
            <span
              style={{
                fontSize: "0.85rem",
                fontWeight: 600,
                color: "var(--text-secondary)",
                textTransform: "uppercase",
              }}
            >
              In Progress
            </span>
            <div className="stats-value" style={{ color: "var(--accent-color)" }}>
              {progressCount}
            </div>
          </div>
          <div
            style={{
              padding: "0.75rem",
              borderRadius: "12px",
              backgroundColor: "rgba(99, 102, 241, 0.1)",
              color: "var(--accent-color)",
            }}
          >
            <PlayCircle size={24} />
          </div>
        </div>

        <div className="card stats-card">
          <div>
            <span
              style={{
                fontSize: "0.85rem",
                fontWeight: 600,
                color: "var(--text-secondary)",
                textTransform: "uppercase",
              }}
            >
              Pending
            </span>
            <div className="stats-value" style={{ color: "var(--warning-color)" }}>
              {pendingCount}
            </div>
          </div>
          <div
            style={{
              padding: "0.75rem",
              borderRadius: "12px",
              backgroundColor: "rgba(245, 158, 11, 0.1)",
              color: "var(--warning-color)",
            }}
          >
            <Hourglass size={24} />
          </div>
        </div>

        <div className="card stats-card">
          <div>
            <span
              style={{
                fontSize: "0.85rem",
                fontWeight: 600,
                color: "var(--text-secondary)",
                textTransform: "uppercase",
              }}
            >
              Missed
            </span>
            <div className="stats-value" style={{ color: "var(--missed-color)" }}>
              {missedCount}
            </div>
          </div>
          <div
            style={{
              padding: "0.75rem",
              borderRadius: "12px",
              backgroundColor: "rgba(139, 92, 246, 0.1)",
              color: "var(--missed-color)",
            }}
          >
            <ClipboardList size={24} />
          </div>
        </div>
      </div>

      {/* Visual Charts Section */}
      <div
        className="card"
        style={{ padding: "2rem", display: "flex", flexDirection: "column", gap: "1.5rem" }}
      >
        <h3 style={{ fontSize: "1.25rem", color: "var(--text-primary)" }}>Status Allocation</h3>
        <div
          style={{
            width: "100%",
            borderTop: "1px solid var(--border-color)",
            padding: "1.5rem 0 0 0",
          }}
        >
          <TaskChart counts={stats.counts} />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
