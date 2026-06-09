import React, { useEffect, useRef, useState } from "react";

import {
  Calendar,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Edit,
  FileDown,
  Paperclip,
  Plus,
  Search,
  Trash2,
} from "lucide-react";

import { deleteTask, downloadExport, getTasks, updateTask } from "../api/tasks";
import type { Task, TaskStatus } from "../api/tasks";
import TaskModal from "../components/TaskModal";

const LIMIT = 10;

export const Tasks: React.FC = () => {
  const [listState, setListState] = useState<{
    tasks: Task[];
    totalCount: number;
    loading: boolean;
    error: string | null;
    exporting: string | null;
  }>({
    tasks: [],
    totalCount: 0,
    loading: true,
    error: null,
    exporting: null,
  });

  // Queries
  const [searchQuery, setSearchQuery] = useState<string>("");
  const debouncedSearchQueryRef = useRef<string>("");

  const [query, setQuery] = useState<{
    statusFilter: TaskStatus | "";
    page: number;
    sortBy: string;
    sortOrder: "asc" | "desc";
    refreshTrigger: number;
  }>({
    statusFilter: "",
    page: 1,
    sortBy: "created_at",
    sortOrder: "desc",
    refreshTrigger: 0,
  });

  const { tasks, totalCount, loading, error, exporting } = listState;
  const { statusFilter, page, sortBy, sortOrder, refreshTrigger } = query;

  // Modal configuration
  const [modalConfig, setModalConfig] = useState<{
    show: boolean;
    mode: "create" | "edit";
    activeTask: Task | null;
  }>({
    show: false,
    mode: "create",
    activeTask: null,
  });

  useEffect(() => {
    let active = true;
    const fetchTasksList = async () => {
      await Promise.resolve();
      if (!active) return;
      setListState((prev) => ({ ...prev, loading: true }));
      try {
        const result = await getTasks(
          statusFilter || undefined,
          debouncedSearchQueryRef.current || undefined,
          page,
          LIMIT,
          sortBy,
          sortOrder
        );
        if (active) {
          setListState((prev) => ({
            ...prev,
            tasks: result.tasks,
            totalCount: result.total_count,
          }));
        }
      } catch (err: unknown) {
        if (active) {
          const errorMsg = err instanceof Error ? err.message : "Failed to load tasks list.";
          setListState((prev) => ({ ...prev, error: errorMsg }));
        }
      } finally {
        if (active) {
          setListState((prev) => ({ ...prev, loading: false }));
        }
      }
    };

    fetchTasksList();
    return () => {
      active = false;
    };
  }, [statusFilter, page, sortBy, sortOrder, refreshTrigger]);

  // Debounced search query triggers
  useEffect(() => {
    const handler = setTimeout(() => {
      debouncedSearchQueryRef.current = searchQuery;
      setQuery((prev) => ({
        ...prev,
        page: 1,
        refreshTrigger: prev.refreshTrigger + 1,
      }));
    }, 400);

    return () => clearTimeout(handler);
  }, [searchQuery]);

  const handleExport = async (type: "pdf" | "excel") => {
    setListState((prev) => ({ ...prev, exporting: type }));
    try {
      await downloadExport(type);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Export failed.";
      alert(errorMsg);
    } finally {
      setListState((prev) => ({ ...prev, exporting: null }));
    }
  };

  const handleSort = (field: string) => {
    let newOrder: "asc" | "desc" = "desc";
    if (sortBy === field) {
      newOrder = sortOrder === "asc" ? "desc" : "asc";
    }
    setQuery((prev) => ({
      ...prev,
      sortBy: field,
      sortOrder: newOrder,
      page: 1,
    }));
  };

  const openCreateModal = () => {
    setModalConfig({
      show: true,
      mode: "create",
      activeTask: null,
    });
  };

  const openEditModal = (task: Task) => {
    setModalConfig({
      show: true,
      mode: "edit",
      activeTask: task,
    });
  };

  const handleCompleteTask = async (task: Task) => {
    try {
      if (task.status === "Pending" || task.status === "Missed") {
        const progressData = new FormData();
        progressData.append("status", "In Progress");
        await updateTask(task.id, progressData);
      }
      const doneData = new FormData();
      doneData.append("status", "Done");
      await updateTask(task.id, doneData);
      setQuery((prev) => ({ ...prev, refreshTrigger: prev.refreshTrigger + 1 }));
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Failed to update task.";
      alert(errorMsg);
    }
  };

  const handleDeleteTask = async (task: Task) => {
    if (!confirm(`Are you sure you want to delete task "${task.task_name}"?`)) return;
    try {
      await deleteTask(task.id);
      setQuery((prev) => ({ ...prev, refreshTrigger: prev.refreshTrigger + 1 }));
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Failed to delete task.";
      alert(errorMsg);
    }
  };

  const totalPages = Math.ceil(totalCount / LIMIT);

  return (
    <div className="fade-in" style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div
        style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}
      >
        <div>
          <h2
            style={{ fontSize: "1.75rem", marginBottom: "0.25rem", color: "var(--text-primary)" }}
          >
            Task Center
          </h2>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
            Add, modify, filter, and export tasks.
          </p>
        </div>
        <button type="button" className="btn btn-primary" onClick={openCreateModal}>
          <Plus size={18} />
          <span>New Task</span>
        </button>
      </div>

      {/* Query Filters & Search */}
      <div className="card filters-bar" style={{ padding: "1rem" }}>
        <div className="search-input-wrapper">
          <Search size={18} className="search-icon" />
          <input
            aria-label="Search tasks by name"
            type="text"
            className="input-field"
            placeholder="Search task by name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", alignItems: "center" }}>
          <select
            className="input-field"
            style={{ width: "160px" }}
            value={statusFilter}
            onChange={(e) => {
              setQuery((prev) => ({
                ...prev,
                statusFilter: e.target.value as TaskStatus | "",
                page: 1,
              }));
            }}
          >
            <option value="">All Statuses</option>
            <option value="Pending">Pending</option>
            <option value="In Progress">In Progress</option>
            <option value="Done">Done</option>
            <option value="Missed">Missed</option>
          </select>

          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => handleExport("excel")}
              disabled={exporting !== null}
              style={{ fontSize: "0.85rem", padding: "0.5rem 1rem" }}
            >
              <FileDown size={14} />
              <span>{exporting === "excel" ? "Exporting..." : "Excel"}</span>
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => handleExport("pdf")}
              disabled={exporting !== null}
              style={{ fontSize: "0.85rem", padding: "0.5rem 1rem" }}
            >
              <FileDown size={14} />
              <span>{exporting === "pdf" ? "Exporting..." : "PDF"}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Table */}
      {error ? (
        <div
          className="card"
          style={{ textAlign: "center", padding: "3rem", color: "var(--danger-color)" }}
        >
          {error}
        </div>
      ) : loading ? (
        <div
          className="card"
          style={{ textAlign: "center", padding: "3rem", color: "var(--text-secondary)" }}
        >
          Loading tasks list...
        </div>
      ) : tasks.length === 0 ? (
        <div
          className="card"
          style={{ textAlign: "center", padding: "3rem", color: "var(--text-secondary)" }}
        >
          No tasks found matching your filter rules.
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ cursor: "pointer" }} onClick={() => handleSort("task_name")}>
                  Task Name{" "}
                  {sortBy === "task_name" &&
                    (sortOrder === "asc" ? (
                      <ChevronUp size={12} style={{ display: "inline" }} />
                    ) : (
                      <ChevronDown size={12} style={{ display: "inline" }} />
                    ))}
                </th>
                <th>Description</th>
                <th
                  style={{ cursor: "pointer", width: "130px" }}
                  onClick={() => handleSort("status")}
                >
                  Status{" "}
                  {sortBy === "status" &&
                    (sortOrder === "asc" ? (
                      <ChevronUp size={12} style={{ display: "inline" }} />
                    ) : (
                      <ChevronDown size={12} style={{ display: "inline" }} />
                    ))}
                </th>
                <th
                  style={{ cursor: "pointer", width: "160px" }}
                  onClick={() => handleSort("expected_end_time")}
                >
                  Deadline{" "}
                  {sortBy === "expected_end_time" &&
                    (sortOrder === "asc" ? (
                      <ChevronUp size={12} style={{ display: "inline" }} />
                    ) : (
                      <ChevronDown size={12} style={{ display: "inline" }} />
                    ))}
                </th>
                <th style={{ width: "110px" }}>Duration</th>
                <th style={{ width: "100px" }}>File</th>
                <th style={{ width: "140px", textAlign: "right" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((task) => (
                <tr key={task.id}>
                  <td style={{ fontWeight: 600 }}>{task.task_name}</td>
                  <td
                    style={{
                      color: "var(--text-secondary)",
                      maxWidth: "250px",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {task.description || "-"}
                  </td>
                  <td>
                    <span
                      className={`badge ${
                        task.status === "Pending"
                          ? "badge-pending"
                          : task.status === "In Progress"
                            ? "badge-progress"
                            : task.status === "Done"
                              ? "badge-done"
                              : "badge-missed"
                      }`}
                    >
                      {task.status}
                    </span>
                  </td>
                  <td>
                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "0.25rem",
                        fontSize: "0.85rem",
                      }}
                    >
                      <Calendar size={14} style={{ color: "var(--text-secondary)" }} />
                      {new Date(task.expected_end_time).toLocaleDateString()}{" "}
                      {new Date(task.expected_end_time).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </td>
                  <td style={{ fontSize: "0.85rem" }}>
                    {task.status === "Done" && task.total_time_taken_seconds !== undefined
                      ? `${Math.round(task.total_time_taken_seconds / 60)}m`
                      : "-"}
                  </td>
                  <td>
                    {task.attachment_path ? (
                      <span title="File Attached" style={{ color: "var(--accent-color)" }}>
                        <Paperclip size={16} />
                      </span>
                    ) : (
                      "-"
                    )}
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <div style={{ display: "inline-flex", gap: "0.5rem" }}>
                      {task.status !== "Done" && (
                        <button
                          type="button"
                          onClick={() => handleCompleteTask(task)}
                          className="btn btn-secondary"
                          style={{ padding: "0.35rem", borderRadius: "6px" }}
                          title="Mark Complete"
                        >
                          <CheckCircle2 size={16} style={{ color: "var(--success-color)" }} />
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => openEditModal(task)}
                        className="btn btn-secondary"
                        style={{ padding: "0.35rem", borderRadius: "6px" }}
                        title="Edit Task"
                      >
                        <Edit size={16} style={{ color: "var(--accent-color)" }} />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeleteTask(task)}
                        className="btn btn-secondary"
                        style={{ padding: "0.35rem", borderRadius: "6px" }}
                        title="Delete Task"
                      >
                        <Trash2 size={16} style={{ color: "var(--danger-color)" }} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination controls */}
      {totalPages > 1 && (
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            gap: "1rem",
            marginTop: "1rem",
          }}
        >
          <button
            type="button"
            className="btn btn-secondary"
            disabled={page === 1}
            onClick={() => setQuery((prev) => ({ ...prev, page: prev.page - 1 }))}
            style={{ padding: "0.5rem 1rem" }}
          >
            Previous
          </button>
          <span style={{ fontSize: "0.9rem", color: "var(--text-secondary)" }}>
            Page <strong>{page}</strong> of {totalPages}
          </span>
          <button
            type="button"
            className="btn btn-secondary"
            disabled={page === totalPages}
            onClick={() => setQuery((prev) => ({ ...prev, page: prev.page + 1 }))}
            style={{ padding: "0.5rem 1rem" }}
          >
            Next
          </button>
        </div>
      )}

      {/* CRUD Form Modal */}
      {modalConfig.show && (
        <TaskModal
          mode={modalConfig.mode}
          activeTask={modalConfig.activeTask}
          onClose={() => setModalConfig((prev) => ({ ...prev, show: false }))}
          onSuccess={() => {
            setModalConfig((prev) => ({ ...prev, show: false }));
            setQuery((prev) => ({ ...prev, refreshTrigger: prev.refreshTrigger + 1 }));
          }}
        />
      )}
    </div>
  );
};

export default Tasks;
