import React, { useState } from "react";

import { Link, useNavigate } from "react-router-dom";
import { CheckSquare, AlertCircle } from "lucide-react";

import { login } from "../api/auth";

interface LoginProps {
  onLoginSuccess: (username: string) => void;
}

export const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const navigate = useNavigate();

  const [username, setUsername] = useState<string>("");
  const [password, setPassword] = useState<string>("");

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Simple validations
    if (!username.trim() || !password.trim()) {
      setError("Both username and password are required fields.");
      return;
    }

    setLoading(true);
    try {
      const user = await login(username, password);
      onLoginSuccess(user.username);
      navigate("/dashboard");
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Invalid username or password.";
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="card glass-card auth-card fade-in">
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <div className="brand" style={{ justifyContent: "center", marginBottom: "0.5rem" }}>
            <CheckSquare size={36} style={{ color: "var(--accent-color)" }} />
            <span style={{ fontSize: "2rem" }}>TodoSphere</span>
          </div>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
            DevOps Minimal Edition Dashboard Login
          </p>
        </div>

        {error && (
          <div className="form-error-alert">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="username">
              Username
            </label>
            <input
              id="username"
              type="text"
              className="input-field"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              className="input-field"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: "100%", marginTop: "1rem" }}
            disabled={loading}
          >
            {loading ? "Authenticating..." : "Login To App"}
          </button>
        </form>

        <div style={{ textAlign: "center", marginTop: "1.5rem", fontSize: "0.875rem" }}>
          <span style={{ color: "var(--text-secondary)" }}>Don&apos;t have an account? </span>
          <Link to="/signup" style={{ fontWeight: 600 }}>
            Sign Up
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Login;
