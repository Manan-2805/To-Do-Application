import client from "./client";

export interface AuditLog {
  id: string;
  user_id?: string;
  action: string;
  entity_type: string;
  entity_id?: string;
  action_metadata?: Record<string, unknown>;

  ip_address?: string;
  user_agent?: string;
  created_at: string;
}

export interface PaginatedAudits {
  audits: AuditLog[];
  total_count: number;
  page: number;
  limit: number;
}

export const getAudits = (
  page = 1,
  limit = 10,
  sortBy = "created_at",
  sortOrder = "desc"
): Promise<PaginatedAudits> => {
  const params = new URLSearchParams();
  params.append("page", String(page));
  params.append("limit", String(limit));
  params.append("sort_by", sortBy);
  params.append("sort_order", sortOrder);

  return client.get<PaginatedAudits>(`/audit/?${params.toString()}`);
};
