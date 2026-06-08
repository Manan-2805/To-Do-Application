import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { CheckSquare, AlertCircle } from "lucide-react";

import { signUp } from "../api/auth";

export const SignUp: React.FC = () => {
  const navigate = useNavigate();
  
  const [username, setUsername] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [confirmPassword, setConfirmPassword] = useState<string>("");
  
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    // Front-end validations
    if (!username.trim() || !password || !confirmPassword) {
      setError("All fields are required.");
      return;
    }

    if (username.length < 3) {
      setError("Username must be at least 3 characters long.");
      return;
    }

    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      setError("Username can only contain alphanumeric characters and underscores.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      await signUp(username, password, confirmPassword);
      setSuccess("Account created successfully! Redirecting to login...");
      setTimeout(() => {
        navigate("/login");
      }, 2000);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Registration failed. Try a different username.";
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
            Create your new TodoSphere account
          </p>
        </div>

        {error && (
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
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div style={{
            padding: "0.75rem 1rem",
            backgroundColor: "rgba(16, 185, 129, 0.1)",
            color: "var(--success-color)",
            borderRadius: "8px",
            fontSize: "0.875rem",
            marginBottom: "1rem",
            fontWeight: 500
          }}>
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              className="input-field"
              placeholder="Min 3 chars, alphanumeric"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              className="input-field"
              placeholder="Min 8 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="confirm_password">Confirm Password</label>
            <input
              id="confirm_password"
              type="password"
              className="input-field"
              placeholder="Re-enter password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
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
            {loading ? "Creating account..." : "Sign Up"}
          </button>
        </form>

        <div style={{ textAlign: "center", marginTop: "1.5rem", fontSize: "0.875rem" }}>
          <span style={{ color: "var(--text-secondary)" }}>Already have an account? </span>
          <Link to="/login" style={{ fontWeight: 600 }}>Login</Link>
        </div>
      </div>
    </div>
  );
};

export default SignUp;
