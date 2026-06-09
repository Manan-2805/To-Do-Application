import { act, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import Header from "./Header";

vi.mock("../api/auth", () => ({
  logout: vi.fn().mockResolvedValue({ success: true }),
}));

describe("Header Component", () => {
  it("renders brand name and navigation links", () => {
    render(
      <MemoryRouter>
        <Header username="TestUser" onLogout={() => {}} />
      </MemoryRouter>
    );

    expect(screen.getByText("TodoSphere")).toBeInTheDocument();
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Tasks")).toBeInTheDocument();
    expect(screen.getByText("Audits")).toBeInTheDocument();
    expect(screen.getByText("Hi,")).toBeInTheDocument();
    expect(screen.getByText("TestUser")).toBeInTheDocument();
  });

  it("calls onLogout on logout click", async () => {
    const handleLogout = vi.fn();
    render(
      <MemoryRouter>
        <Header username="TestUser" onLogout={handleLogout} />
      </MemoryRouter>
    );

    const logoutBtn = screen.getByRole("button", { name: /logout/i });

    await act(async () => {
      fireEvent.click(logoutBtn);
    });

    await vi.waitFor(() => {
      expect(handleLogout).toHaveBeenCalled();
    });
  });
});
