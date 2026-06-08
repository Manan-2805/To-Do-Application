import client from "./client";

export type TaskStatus = "Pending" | "In Progress" | "Done" | "Missed";

export interface Task {
  id: string;
  task_name: string;
  description?: string;
  status: TaskStatus;
  start_time: string;
  expected_end_time: string;
  actual_end_time?: string;
  attachment_path?: string;
  total_time_taken_seconds?: number;
  created_at: string;
  updated_at: string;
}

export interface PaginatedTasks {
  tasks: Task[];
  total_count: number;
  page: number;
  limit: number;
}

export interface DashboardStats {
  counts: Record<TaskStatus, number>;
  total: number;
}

export const getTasks = (
  status?: TaskStatus,
  search?: string,
  page = 1,
  limit = 10,
  sortBy = "created_at",
  sortOrder = "desc"
): Promise<PaginatedTasks> => {
  const params = new URLSearchParams();
  if (status) params.append("status", status);
  if (search) params.append("search", search);
  params.append("page", String(page));
  params.append("limit", String(limit));
  params.append("sort_by", sortBy);
  params.append("sort_order", sortOrder);

  return client.get<PaginatedTasks>(`/tasks/?${params.toString()}`);
};

export const getTask = (taskId: string): Promise<Task> => {
  return client.get<Task>(`/tasks/${taskId}`);
};

export const createTask = (formData: FormData): Promise<Task> => {
  return client.post<Task>("/tasks/", formData);
};

export const updateTask = (taskId: string, formData: FormData): Promise<Task> => {
  return client.put<Task>(`/tasks/${taskId}`, formData);
};

export const deleteTask = (taskId: string): Promise<{ message: string }> => {
  return client.delete<{ message: string }>(`/tasks/${taskId}`);
};

export const getStats = (): Promise<DashboardStats> => {
  return client.get<DashboardStats>("/tasks/stats");
};

export const downloadExport = async (type: "pdf" | "excel"): Promise<void> => {
  const baseUrl = (import.meta.env.VITE_API_URL || "/api/v1").replace(/\/$/, "");
  const response = await fetch(`${baseUrl}/tasks/export/${type}`, {
    credentials: "include",
  });
  
  if (!response.ok) {
    throw new Error(`Export failed: ${response.statusText}`);
  }
  
  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = downloadUrl;
  a.download = `todosphere_tasks_${new Date().toISOString().slice(0, 10)}.${type === "excel" ? "xlsx" : "pdf"}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(downloadUrl);
};
