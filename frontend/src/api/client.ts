export interface ErrorDetail {
  code: string;
  message: string;
  details?: unknown;
}

export interface APIResponse<T> {
  success: boolean;
  data: T | null;
  error: ErrorDetail | null;
  correlation_id: string;
}

const BASE_URL = (import.meta.env.VITE_API_URL || "/api/v1").replace(/\/$/, "");

class APIClient {
  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const url = `${BASE_URL}${path}`;
    
    // Ensure credentials: "include" so HttpOnly cookies are transmitted
    const defaultOptions: RequestInit = {
      credentials: "include",
      ...options,
      headers: {
        ...options.headers,
      },
    };

    // If body is not FormData, set Content-Type to application/json
    if (defaultOptions.body && !(defaultOptions.body instanceof FormData)) {
      defaultOptions.headers = {
        "Content-Type": "application/json",
        ...defaultOptions.headers,
      };
    }

    const response = await fetch(url, defaultOptions);
    
    // Handle HTTP status code 401 with potential silent refresh trigger
    if (response.status === 401 && !path.includes("/auth/refresh") && !path.includes("/auth/login")) {
      try {
        const refreshOk = await this.refreshToken();
        if (refreshOk) {
          // Retry original request
          return await this.request<T>(path, options);
        }
      } catch {
        // Clear session or bubble up
      }
      throw new Error("Unauthorized");
    }

    if (response.status === 204) {
      return {} as T;
    }

    let result: APIResponse<T>;
    try {
      result = await response.json();
    } catch (err) {
      throw new Error(`Failed to parse response: ${response.statusText}`, { cause: err });
    }

    if (!result.success) {
      const errorMsg = result.error?.message || "An unexpected error occurred.";
      interface APIError extends Error {
        code?: string;
        details?: unknown;
      }
      const error = new Error(errorMsg) as APIError;
      error.code = result.error?.code;
      error.details = result.error?.details;
      throw error;
    }

    return result.data as T;
  }

  private async refreshToken(): Promise<boolean> {
    const url = `${BASE_URL}/auth/refresh`;
    const response = await fetch(url, {
      method: "POST",
      credentials: "include",
    });
    return response.ok;
  }

  public get<T>(path: string, headers?: HeadersInit): Promise<T> {
    return this.request<T>(path, { method: "GET", headers });
  }

  public post<T>(path: string, body?: unknown, headers?: HeadersInit): Promise<T> {
    const isFormData = body instanceof FormData;
    return this.request<T>(path, {
      method: "POST",
      body: isFormData ? body : JSON.stringify(body),
      headers,
    });
  }

  public put<T>(path: string, body?: unknown, headers?: HeadersInit): Promise<T> {
    const isFormData = body instanceof FormData;
    return this.request<T>(path, {
      method: "PUT",
      body: isFormData ? body : JSON.stringify(body),
      headers,
    });
  }

  public delete<T>(path: string, headers?: HeadersInit): Promise<T> {
    return this.request<T>(path, { method: "DELETE", headers });
  }
}

export const client = new APIClient();
export default client;
