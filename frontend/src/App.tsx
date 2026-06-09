import React, { useEffect, useState } from "react";

import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { getMe } from "./api/auth";
import Header from "./components/Header";
import Audit from "./pages/Audit";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import SignUp from "./pages/SignUp";
import Tasks from "./pages/Tasks";

export const App: React.FC = () => {
  const [username, setUsername] = useState<string>("");
  const [authenticated, setAuthenticated] = useState<boolean>(false);
  const [checkingSession, setCheckingSession] = useState<boolean>(true);

  useEffect(() => {
    const checkSession = async () => {
      try {
        const user = await getMe();
        setUsername(user.username);
        setAuthenticated(true);
      } catch {
        setAuthenticated(false);
      } finally {
        setCheckingSession(false);
      }
    };

    // react-doctor-disable-next-line react-doctor/no-initialize-state
    checkSession();
  }, []);

  const handleLoginSuccess = (user: string) => {
    setUsername(user);
    setAuthenticated(true);
  };

  const handleLogout = () => {
    setUsername("");
    setAuthenticated(false);
  };

  if (checkingSession) {
    return (
      <div
        style={{
          display: "flex",
          width: "100vw",
          height: "100vh",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "var(--bg-primary)",
        }}
      >
        <p style={{ color: "var(--text-secondary)", fontWeight: 500 }}>
          Initializing TodoSphere Session...
        </p>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        {/* Public Auth Routes */}
        <Route
          path="/login"
          element={
            !authenticated ? (
              <Login onLoginSuccess={handleLoginSuccess} />
            ) : (
              <Navigate to="/dashboard" />
            )
          }
        />
        <Route
          path="/signup"
          element={!authenticated ? <SignUp /> : <Navigate to="/dashboard" />}
        />

        {/* Protected Dashboard Routes */}
        <Route
          path="/dashboard"
          element={
            authenticated ? (
              <div className="main-content">
                <Header username={username} onLogout={handleLogout} />
                <Dashboard />
              </div>
            ) : (
              <Navigate to="/login" />
            )
          }
        />

        <Route
          path="/tasks"
          element={
            authenticated ? (
              <div className="main-content">
                <Header username={username} onLogout={handleLogout} />
                <Tasks />
              </div>
            ) : (
              <Navigate to="/login" />
            )
          }
        />

        <Route
          path="/audit"
          element={
            authenticated ? (
              <div className="main-content">
                <Header username={username} onLogout={handleLogout} />
                <Audit />
              </div>
            ) : (
              <Navigate to="/login" />
            )
          }
        />

        {/* Fallback routing */}
        <Route path="*" element={<Navigate to={authenticated ? "/dashboard" : "/login"} />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
