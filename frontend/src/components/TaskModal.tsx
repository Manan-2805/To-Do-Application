import React, { useRef, useState } from "react";

import { X } from "lucide-react";

import { createTask, updateTask } from "../api/tasks";
import type { Task, TaskStatus } from "../api/tasks";

interface TaskModalProps {
  mode: "create" | "edit";
  activeTask: Task | null;
  onClose: () => void;
  onSuccess: () => void;
}

export const TaskModal: React.FC<TaskModalProps> = ({ mode, activeTask, onClose, onSuccess }) => {
  const [formState, setFormState] = useState<{
    taskName: string;
    description: string;
    expectedEndTime: string;
    taskStatus: TaskStatus;
    formError: string | null;
    formSubmitting: boolean;
  }>(() => {
    let initialEndTime: string;
    if (activeTask) {
      const dateStr = new Date(activeTask.expected_end_time);
      dateStr.setMinutes(dateStr.getMinutes() - dateStr.getTimezoneOffset());
      initialEndTime = dateStr.toISOString().slice(0, 16);
    } else {
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      tomorrow.setMinutes(tomorrow.getMinutes() - tomorrow.getTimezoneOffset());
      initialEndTime = tomorrow.toISOString().slice(0, 16);
    }

    return {
      taskName: activeTask?.task_name || "",
      description: activeTask?.description || "",
      expectedEndTime: initialEndTime,
      taskStatus: activeTask?.status || "Pending",
      formError: null,
      formSubmitting: false,
    };
  });

  const { taskName, description, expectedEndTime, taskStatus, formError, formSubmitting } =
    formState;

  const attachmentFileRef = useRef<File | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const allowed = [".jpg", ".jpeg", ".png", ".webp"];
    const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    if (!allowed.includes(ext)) {
      setFormState((prev) => ({
        ...prev,
        formError: "Format is invalid. Only JPG, JPEG, PNG, WEBP allowed.",
      }));
      attachmentFileRef.current = null;
      e.target.value = "";
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setFormState((prev) => ({
        ...prev,
        formError: "File size cannot exceed 5 MB.",
      }));
      attachmentFileRef.current = null;
      e.target.value = "";
      return;
    }

    setFormState((prev) => ({ ...prev, formError: null }));
    attachmentFileRef.current = file;
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormState((prev) => ({ ...prev, formError: null }));

    if (!taskName.trim()) {
      setFormState((prev) => ({ ...prev, formError: "Task name is required." }));
      return;
    }
    if (!expectedEndTime) {
      setFormState((prev) => ({ ...prev, formError: "Deadline is required." }));
      return;
    }

    const formData = new FormData();
    formData.append("task_name", taskName.trim());
    formData.append("description", description.trim());
    formData.append("expected_end_time", new Date(expectedEndTime).toISOString());
    if (attachmentFileRef.current) {
      formData.append("attachment", attachmentFileRef.current);
    }

    setFormState((prev) => ({ ...prev, formSubmitting: true }));
    try {
      if (mode === "create") {
        await createTask(formData);
      } else if (mode === "edit" && activeTask) {
        formData.append("status", taskStatus);
        await updateTask(activeTask.id, formData);
      }
      onSuccess();
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Failed to save task.";
      setFormState((prev) => ({ ...prev, formError: errorMsg }));
    } finally {
      setFormState((prev) => ({ ...prev, formSubmitting: false }));
    }
  };

  return (
    <div className="modal-overlay">
      <div
        className="card glass-card fade-in"
        style={{ width: "95%", maxWidth: "500px", position: "relative", padding: "2rem" }}
      >
        <button
          type="button"
          onClick={onClose}
          style={{
            position: "absolute",
            top: "1rem",
            right: "1rem",
            background: "none",
            border: "none",
            cursor: "pointer",
            color: "var(--text-secondary)",
          }}
          aria-label="Close modal"
        >
          <X size={20} />
        </button>

        <h3 style={{ fontSize: "1.5rem", marginBottom: "1.5rem", color: "var(--text-primary)" }}>
          {mode === "create" ? "Create New Task" : "Edit Task"}
        </h3>

        {formError && (
          <div className="form-error-alert">
            <AlertCircle size={16} />
            <span>{formError}</span>
          </div>
        )}

        <form onSubmit={handleFormSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="taskName">
              Task Name
            </label>
            <input
              id="taskName"
              type="text"
              className="input-field"
              value={taskName}
              onChange={(e) => setFormState((prev) => ({ ...prev, taskName: e.target.value }))}
              disabled={formSubmitting}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="description">
              Description
            </label>
            <textarea
              id="description"
              className="input-field"
              style={{ minHeight: "80px", resize: "vertical" }}
              value={description}
              onChange={(e) => setFormState((prev) => ({ ...prev, description: e.target.value }))}
              disabled={formSubmitting}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="expectedEndTime">
              Deadline
            </label>
            <input
              id="expectedEndTime"
              type="datetime-local"
              className="input-field"
              value={expectedEndTime}
              onChange={(e) =>
                setFormState((prev) => ({ ...prev, expectedEndTime: e.target.value }))
              }
              disabled={formSubmitting}
              required
            />
          </div>

          {mode === "edit" && activeTask && activeTask.status !== "Done" && (
            <div className="form-group">
              <label className="form-label" htmlFor="taskStatus">
                Status
              </label>
              <select
                id="taskStatus"
                className="input-field"
                value={taskStatus}
                onChange={(e) =>
                  setFormState((prev) => ({
                    ...prev,
                    taskStatus: e.target.value as TaskStatus,
                  }))
                }
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
              Attachment{" "}
              <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                (Max 5MB: JPG, PNG, WEBP)
              </span>
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

          <div
            style={{
              display: "flex",
              gap: "1rem",
              marginTop: "2rem",
              justifyContent: "flex-end",
            }}
          >
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={formSubmitting}
            >
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={formSubmitting}>
              {formSubmitting ? "Saving..." : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const AlertCircle = ({ size }: { size: number }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <circle cx="12" cy="12" r="10" />
    <line x1="12" y1="8" x2="12" y2="12" />
    <line x1="12" y1="16" x2="12.01" y2="16" />
  </svg>
);

export default TaskModal;
