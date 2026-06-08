import React, { useEffect, useState } from "react";

import {
  Calendar, CheckCircle2, ChevronDown, ChevronUp, Edit,
  FileDown, Paperclip, Plus, Search, Trash2, X
} from "lucide-react";

import {
  createTask, deleteTask, downloadExport, getTasks,
  updateTask
} from "../api/tasks";
import type { Task, TaskStatus } from "../api/tasks";

export const Tasks: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);

  // Queries
  const [statusFilter, setStatusFilter] = useState<TaskStatus | "">("");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState<string>("");
  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [limit] = useState<number>(10);
  const [sortBy, setSortBy] = useState<string>("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  // UX states
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState<string | null>(null);

  // Form Modal States
  const [showModal, setShowModal] = useState<boolean>(false);
  const [modalMode, setModalMode] = useState<"create" | "edit">("create");
  const [activeTask, setActiveTask] = useState<Task | null>(null);

  // Form fields
  const [taskName, setTaskName] = useState<string>("");
  const [description, setDescription] = useState<string>("");
  const [expectedEndTime, setExpectedEndTime] = useState<string>("");
  const [taskStatus, setTaskStatus] = useState<TaskStatus>("Pending");
  const [attachmentFile, setAttachmentFile] = useState<File | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [formSubmitting, setFormSubmitting] = useState<boolean>(false);

  useEffect(() => {
    let active = true;
    const fetchTasksList = async () => {
      await Promise.resolve();
      if (!active) return;
      setLoading(true);
      try {
        const result = await getTasks(
          statusFilter || undefined,
          debouncedSearchQuery || undefined,
          page,
          limit,
          sortBy,
          sortOrder
        );
        if (active) {
          setTasks(result.tasks);
          setTotalCount(result.total_count);
        }
      } catch (err: unknown) {
        if (active) {
          const errorMsg = err instanceof Error ? err.message : "Failed to load tasks list.";
          setError(errorMsg);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    fetchTasksList();
    return () => {
      active = false;
    };
  }, [statusFilter, debouncedSearchQuery, page, limit, sortBy, sortOrder, refreshTrigger]);

  // Debounced search query triggers
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearchQuery(searchQuery);
      setPage(1);
    }, 400);

    return () => clearTimeout(handler);
  }, [searchQuery]);

  const handleExport = async (type: "pdf" | "excel") => {
    setExporting(type);
    try {
      await downloadExport(type);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Export failed.";
      alert(errorMsg);
    } finally {
      setExporting(null);
    }
  };

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(field);
      setSortOrder("desc");
    }
    setPage(1);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Client Validation
    const allowed = [".jpg", ".jpeg", ".png", ".webp"];
    const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    if (!allowed.includes(ext)) {
      setFormError("Format is invalid. Only JPG, JPEG, PNG, WEBP allowed.");
      setAttachmentFile(null);
      e.target.value = "";
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setFormError("File size cannot exceed 5 MB.");
      setAttachmentFile(null);
      e.target.value = "";
      return;
    }

    setFormError(null);
    setAttachmentFile(file);
  };

  const openCreateModal = () => {
    setModalMode("create");
    setActiveTask(null);
    setTaskName("");
    setDescription("");
    // Default deadline to tomorrow
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setMinutes(tomorrow.getMinutes() - tomorrow.getTimezoneOffset());
    setExpectedEndTime(tomorrow.toISOString().slice(0, 16));
    setTaskStatus("Pending");
    setAttachmentFile(null);
    setFormError(null);
    setShowModal(true);
  };

  const openEditModal = (task: Task) => {
    setModalMode("edit");
    setActiveTask(task);
    setTaskName(task.task_name);
    setDescription(task.description || "");
    const dateStr = new Date(task.expected_end_time);
    dateStr.setMinutes(dateStr.getMinutes() - dateStr.getTimezoneOffset());
    setExpectedEndTime(dateStr.toISOString().slice(0, 16));
    setTaskStatus(task.status);
    setAttachmentFile(null);
    setFormError(null);
    setShowModal(true);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!taskName.trim()) {
      setFormError("Task name is required.");
      return;
    }
    if (!expectedEndTime) {
      setFormError("Deadline is required.");
      return;
    }

    const formData = new FormData();
    formData.append("task_name", taskName.trim());
    formData.append("description", description.trim());
    formData.append("expected_end_time", new Date(expectedEndTime).toISOString());
    if (attachmentFile) {
      formData.append("attachment", attachmentFile);
    }

    setFormSubmitting(true);
    try {
      if (modalMode === "create") {
        await createTask(formData);
      } else if (modalMode === "edit" && activeTask) {
        formData.append("status", taskStatus);
        await updateTask(activeTask.id, formData);
      }
      setShowModal(false);
      setRefreshTrigger(prev => prev + 1);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Failed to save task.";
      setFormError(errorMsg);
    } finally {
      setFormSubmitting(false);
    }
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
      setRefreshTrigger(prev => prev + 1);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Failed to update task.";
      alert(errorMsg);
    }
  };

  const handleDeleteTask = async (task: Task) => {
    if (!confirm(`Are you sure you want to delete task "${task.task_name}"?`)) return;
    try {
      await deleteTask(task.id);
      setRefreshTrigger(prev => prev + 1);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Failed to delete task.";
      alert(errorMsg);
    }
  };

  const totalPages = Math.ceil(totalCount / limit);

  return (
    <div className="fade-in" style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <h2 style={{ fontSize: "1.75rem", marginBottom: "0.25rem", color: "var(--text-primary)" }}>Task Center</h2>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
            Add, modify, filter, and export tasks.
          </p>
        </div>
        <button className="btn btn-primary" onClick={openCreateModal}>
          <Plus size={18} />
          <span>New Task</span>
        </button>
      </div>

      {/* Query Filters & Search */}
      <div className="card filters-bar" style={{ padding: "1rem" }}>
        <div className="search-input-wrapper">
          <Search size={18} className="search-icon" />
          <input
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
              setStatusFilter(e.target.value as TaskStatus | "");
              setPage(1);
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
              className="btn btn-secondary"
              onClick={() => handleExport("excel")}
              disabled={exporting !== null}
              style={{ fontSize: "0.85rem", padding: "0.5rem 1rem" }}
            >
              <FileDown size={14} />
              <span>{exporting === "excel" ? "Exporting..." : "Excel"}</span>
            </button>
            <button
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
        <div className="card" style={{ textAlign: "center", padding: "3rem", color: "var(--danger-color)" }}>
          {error}
        </div>
      ) : loading ? (
        <div className="card" style={{ textAlign: "center", padding: "3rem", color: "var(--text-secondary)" }}>
          Loading tasks list...
        </div>
      ) : tasks.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: "3rem", color: "var(--text-secondary)" }}>
          No tasks found matching your filter rules.
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ cursor: "pointer" }} onClick={() => handleSort("task_name")}>
                  Task Name {sortBy === "task_name" && (sortOrder === "asc" ? <ChevronUp size={12} style={{ display: "inline" }} /> : <ChevronDown size={12} style={{ display: "inline" }} />)}
                </th>
                <th>Description</th>
                <th style={{ cursor: "pointer", width: "130px" }} onClick={() => handleSort("status")}>
                  Status {sortBy === "status" && (sortOrder === "asc" ? <ChevronUp size={12} style={{ display: "inline" }} /> : <ChevronDown size={12} style={{ display: "inline" }} />)}
                </th>
                <th style={{ cursor: "pointer", width: "160px" }} onClick={() => handleSort("expected_end_time")}>
                  Deadline {sortBy === "expected_end_time" && (sortOrder === "asc" ? <ChevronUp size={12} style={{ display: "inline" }} /> : <ChevronDown size={12} style={{ display: "inline" }} />)}
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
                  <td style={{ color: "var(--text-secondary)", maxWidth: "250px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {task.description || "-"}
                  </td>
                  <td>
                    <span className={`badge ${task.status === "Pending" ? "badge-pending" :
                        task.status === "In Progress" ? "badge-progress" :
                          task.status === "Done" ? "badge-done" : "badge-missed"
                      }`}>
                      {task.status}
                    </span>
                  </td>
                  <td>
                    <span style={{ display: "inline-flex", alignItems: "center", gap: "0.25rem", fontSize: "0.85rem" }}>
                      <Calendar size={14} style={{ color: "var(--text-secondary)" }} />
                      {new Date(task.expected_end_time).toLocaleDateString()} {new Date(task.expected_end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
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
                    ) : "-"}
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <div style={{ display: "inline-flex", gap: "0.5rem" }}>
                      {task.status !== "Done" && (
                        <button
                          onClick={() => handleCompleteTask(task)}
                          className="btn btn-secondary"
                          style={{ padding: "0.35rem", borderRadius: "6px" }}
                          title="Mark Complete"
                        >
                          <CheckCircle2 size={16} style={{ color: "var(--success-color)" }} />
                        </button>
                      )}
                      <button
                        onClick={() => openEditModal(task)}
                        className="btn btn-secondary"
                        style={{ padding: "0.35rem", borderRadius: "6px" }}
                        title="Edit Task"
                      >
                        <Edit size={16} style={{ color: "var(--accent-color)" }} />
                      </button>
                      <button
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
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: "1rem", marginTop: "1rem" }}>
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

      {/* CRUD Form Modal */}
      {showModal && (
        <div style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: "rgba(0,0,0,0.5)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 1000
        }}>
          <div className="card glass-card fade-in" style={{ width: "95%", maxWidth: "500px", position: "relative", padding: "2rem" }}>
            <button
              onClick={() => setShowModal(false)}
              style={{
                position: "absolute",
                top: "1rem",
                right: "1rem",
                background: "none",
                border: "none",
                cursor: "pointer",
                color: "var(--text-secondary)"
              }}
            >
              <X size={20} />
            </button>

            <h3 style={{ fontSize: "1.5rem", marginBottom: "1.5rem", color: "var(--text-primary)" }}>
              {modalMode === "create" ? "Create New Task" : "Edit Task"}
            </h3>

            {formError && (
              <div style={{
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                padding: "0.75rem 1rem",
                backgroundColor: "rgba(239, 68, 68, 0.1)",
                color: "var(--danger-color)",
                borderRadius: "8px",
                fontSize: "0.875rem",
                marginBottom: "1rem"
              }}>
                <AlertCircle size={16} />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleFormSubmit}>
              <div className="form-group">
                <label className="form-label" htmlFor="taskName">Task Name</label>
                <input
                  id="taskName"
                  type="text"
                  className="input-field"
                  value={taskName}
                  onChange={(e) => setTaskName(e.target.value)}
                  disabled={formSubmitting}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="description">Description</label>
                <textarea
                  id="description"
                  className="input-field"
                  style={{ minHeight: "80px", resize: "vertical" }}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  disabled={formSubmitting}
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="expectedEndTime">Deadline</label>
                <input
                  id="expectedEndTime"
                  type="datetime-local"
                  className="input-field"
                  value={expectedEndTime}
                  onChange={(e) => setExpectedEndTime(e.target.value)}
                  disabled={formSubmitting}
                  required
                />
              </div>

              {modalMode === "edit" && activeTask && activeTask.status !== "Done" && (
                <div className="form-group">
                  <label className="form-label" htmlFor="taskStatus">Status</label>
                  <select
                    id="taskStatus"
                    className="input-field"
                    value={taskStatus}
                    onChange={(e) => setTaskStatus(e.target.value as TaskStatus)}
                    disabled={formSubmitting}
                  >
                    <option value="Pending">Pending</option>
                    <option value="In Progress">In Progress</option>
                    <option value="Done">Done</option>
                    <option value="Missed">Missed</option>
                  </select>
                </div>
              )}

              <div className="form-group">
                <label className="form-label" htmlFor="attachment">
                  Attachment <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>(Max 5MB: JPG, PNG, WEBP)</span>
                </label>
                <input
                  id="attachment"
                  type="file"
                  className="input-field"
                  onChange={handleFileChange}
                  disabled={formSubmitting}
                  accept=".jpg,.jpeg,.png,.webp"
                />
              </div>

              <div style={{ display: "flex", gap: "1rem", marginTop: "2rem", justifyContent: "flex-end" }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowModal(false)}
                  disabled={formSubmitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={formSubmitting}
                >
                  {formSubmitting ? "Saving..." : "Save"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// Alert circle dummy helper
const AlertCircle = ({ size }: { size: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="8" x2="12" y2="12" />
    <line x1="12" y1="16" x2="12.01" y2="16" />
  </svg>
);

export default Tasks;
