import React from "react";

interface TaskChartProps {
  counts: Record<string, number>;
}

// Colors mapping
const COLORS = {
  Pending: "#f59e0b",
  "In Progress": "#6366f1",
  Done: "#10b981",
  Missed: "#8b5cf6",
};

export const TaskChart: React.FC<TaskChartProps> = ({ counts }) => {
  const pending = counts["Pending"] || 0;
  const inProgress = counts["In Progress"] || 0;
  const done = counts["Done"] || 0;
  const missed = counts["Missed"] || 0;

  const total = pending + inProgress + done + missed;

  if (total === 0) {
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          height: "240px",
        }}
      >
        <svg width="160" height="160" viewBox="0 0 160 160">
          <circle
            cx="80"
            cy="80"
            r="60"
            fill="none"
            stroke="var(--border-color)"
            strokeWidth="20"
          />
        </svg>
        <span style={{ marginTop: "1rem", color: "var(--text-secondary)", fontSize: "0.875rem" }}>
          No tasks created yet
        </span>
      </div>
    );
  }

  // Draw concentric donut segments using stroke-dasharray/stroke-dashoffset on circles
  // Circle perimeter = 2 * PI * r = 2 * 3.14159 * 50 = 314.16
  const r = 50;
  const cx = 80;
  const cy = 80;
  const perimeter = 2 * Math.PI * r;

  const data = [
    { label: "Done" as const, value: done, color: COLORS["Done"] },
    { label: "In Progress" as const, value: inProgress, color: COLORS["In Progress"] },
    { label: "Pending" as const, value: pending, color: COLORS["Pending"] },
    { label: "Missed" as const, value: missed, color: COLORS["Missed"] },
  ].filter((d) => d.value > 0);

  let accumulatedPercent = 0;

  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        alignItems: "center",
        justifyContent: "center",
        gap: "2rem",
      }}
    >
      <div style={{ position: "relative", width: "160px", height: "160px" }}>
        <svg
          width="100%"
          height="100%"
          viewBox="0 0 160 160"
          style={{ transform: "rotate(-90deg)" }}
        >
          {data.map((item) => {
            const percent = item.value / total;
            const dashArray = `${percent * perimeter} ${perimeter}`;
            const dashOffset = -accumulatedPercent * perimeter;
            accumulatedPercent += percent;

            return (
              <circle
                key={item.label}
                cx={cx}
                cy={cy}
                r={r}
                fill="none"
                stroke={item.color}
                strokeWidth="16"
                strokeDasharray={dashArray}
                strokeDashoffset={dashOffset}
                style={{ transition: "stroke-dashoffset 0.5s ease" }}
              />
            );
          })}
        </svg>
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
          }}
        >
          <span style={{ fontSize: "1.75rem", fontWeight: 700, fontFamily: "var(--font-display)" }}>
            {total}
          </span>
          <span
            style={{
              fontSize: "0.75rem",
              color: "var(--text-secondary)",
              textTransform: "uppercase",
              fontWeight: 600,
            }}
          >
            Tasks
          </span>
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        {data.map((item) => (
          <div
            key={item.label}
            style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.875rem" }}
          >
            <span
              style={{
                width: "12px",
                height: "12px",
                borderRadius: "3px",
                backgroundColor: item.color,
              }}
            />
            <span style={{ color: "var(--text-secondary)", fontWeight: 550, width: "90px" }}>
              {item.label}
            </span>
            <span style={{ fontWeight: 700 }}>{item.value}</span>
            <span style={{ color: "var(--text-secondary)", fontSize: "0.75rem" }}>
              ({Math.round((item.value / total) * 100)}%)
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TaskChart;
