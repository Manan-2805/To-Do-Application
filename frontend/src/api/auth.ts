import client from "./client";

export interface User {
  id: string;
  username: string;
  created_at: string;
  updated_at: string;
}

export const signUp = (username: string, password: string, confirmPassword: string): Promise<User> => {
  return client.post<User>("/auth/signup", { username, password, confirm_password: confirmPassword });
};

export const login = (username: string, password: string): Promise<User> => {
  return client.post<User>("/auth/login", { username, password });
};

export const logout = (): Promise<{ message: string }> => {
  return client.post<{ message: string }>("/auth/logout");
};

export const getMe = (): Promise<User> => {
  return client.get<User>("/auth/me");
};
