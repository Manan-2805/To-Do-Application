import React, { useEffect, useState } from "react";

import { Terminal } from "lucide-react";

import { getAudits } from "../api/audit";
import type { AuditLog } from "../api/audit";

export const Audit: React.FC = () => {
  const [audits, setAudits] = useState<AuditLog[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [limit] = useState<number>(10);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const fetchAudits = async () => {
      await Promise.resolve();
      if (!active) return;
      setLoading(true);
      try {
        const result = await getAudits(page, limit);
        if (active) {
          setAudits(result.audits);
          setTotalCount(result.total_count);
        }
      } catch (err: unknown) {
        if (active) {
          const errorMsg = err instanceof Error ? err.message : "Failed to load audit history logs.";
          setError(errorMsg);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    fetchAudits();
    return () => {
      active = false;
    };
  }, [page, limit]);

  const totalPages = Math.ceil(totalCount / limit);

  return (
    <div className="fade-in" style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div>
        <h2 style={{ fontSize: "1.75rem", marginBottom: "0.25rem", color: "var(--text-primary)" }}>Audit Trails</h2>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
          Full DevOps logging detailing user actions, entity mutations, IP, and User-Agent parameters.
        </p>
      </div>

      {error ? (
        <div className="card" style={{ textAlign: "center", padding: "3rem", color: "var(--danger-color)" }}>
          {error}
        </div>
      ) : loading ? (
        <div className="card" style={{ textAlign: "center", padding: "3rem", color: "var(--text-secondary)" }}>
          Loading audit trails...
        </div>
      ) : audits.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: "3rem", color: "var(--text-secondary)" }}>
          No audits found in the database.
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: "180px" }}>Timestamp</th>
                  <th style={{ width: "120px" }}>Action</th>
                  <th style={{ width: "120px" }}>Entity Type</th>
                  <th style={{ width: "220px" }}>IP Address & UA</th>
                  <th>Metadata</th>
                </tr>
              </thead>
              <tbody>
                {audits.map((log) => (
                  <tr key={log.id}>
                    <td>
                      <span style={{ fontSize: "0.85rem", fontWeight: 550 }}>
                        {new Date(log.created_at).toLocaleString()}
                      </span>
                    </td>
                    <td>
                      <span style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "0.25rem",
                        fontSize: "0.75rem",
                        fontWeight: 700,
                        textTransform: "uppercase",
                        color: log.action.includes("delete") ? "var(--danger-color)" :
                          log.action.includes("create") || log.action.includes("signup") ? "var(--success-color)" :
                            "var(--accent-color)"
                      }}>
                        <Terminal size={12} />
                        {log.action}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: "0.85rem", textTransform: "capitalize" }}>{log.entity_type}</span>
                    </td>
                    <td>
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.15rem" }}>
                        <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>{log.ip_address || "127.0.0.1"}</span>
                        <span style={{
                          fontSize: "0.7rem",
                          color: "var(--text-secondary)",
                          maxWidth: "200px",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap"
                        }} title={log.user_agent}>
                          {log.user_agent || "Unknown Agent"}
                        </span>
                      </div>
                    </td>
                    <td>
                      {log.action_metadata ? (
                        <pre style={{
                          margin: 0,
                          padding: "0.4rem 0.6rem",
                          backgroundColor: "var(--bg-primary)",
                          border: "1px solid var(--border-color)",
                          borderRadius: "6px",
                          fontSize: "0.75rem",
                          fontFamily: "monospace",
                          overflowX: "auto",
                          color: "var(--text-primary)"
                        }}>
                          {JSON.stringify(log.action_metadata)}
                        </pre>
                      ) : (
                        <span style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>-</span>
                      )}
                    </td>

                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: "1rem", marginTop: "0.5rem" }}>
              <button
                className="btn btn-secondary"
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
                style={{ padding: "0.5rem 1rem" }}
              >
                Previous
              </button>
              <span style={{ fontSize: "0.9rem", color: "var(--text-secondary)" }}>
                Page <strong>{page}</strong> of {totalPages}
              </span>
              <button
                className="btn btn-secondary"
                disabled={page === totalPages}
                onClick={() => setPage(page + 1)}
                style={{ padding: "0.5rem 1rem" }}
              >
                Next
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Audit;
