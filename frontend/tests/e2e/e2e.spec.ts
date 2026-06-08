import { test, expect } from "@playwright/test";

test.describe("TodoSphere End-to-End Flow", () => {
  const username = `e2e_user_${Date.now()}`;
  const password = "Password123!";
  const taskName = `E2E Playwright Task_${Date.now()}`;

  test("User lifecycle: signup, login, task management, dashboard and audit check", async ({ page }) => {
    page.on("console", msg => {
      const text = msg.text();
      if (text.includes("Failed to load resource") && text.includes("401")) {
        return;
      }
      console.log("BROWSER CONSOLE:", text);
    });
    page.on("response", async response => {
      const url = response.url();
      const status = response.status();
      if (status >= 400) {
        if (status === 401 && (url.includes("/api/v1/auth/me") || url.includes("/api/v1/auth/refresh"))) {
          // Suppressed expected unauthenticated session check logs
          return;
        }
        try {
          console.log("HTTP ERROR:", url, status, await response.text());
        } catch {
          console.log("HTTP ERROR (could not read body):", url, status);
        }
      }
    });

    // 1. Sign Up a User
    await page.goto("/signup");
    await expect(page).toHaveTitle(/TodoSphere/);
    
    await page.fill("#username", username);
    await page.fill("#password", password);
    await page.fill("#confirm_password", password);
    await page.click('button[type="submit"]');

    // Wait for redirect to login page
    await page.waitForURL("**/login");

    // 2. Log In
    await page.fill("#username", username);
    await page.fill("#password", password);
    await page.click('button[type="submit"]');
    
    // Wait for redirect to dashboard
    await page.waitForURL("**/dashboard");
    await expect(page.locator("h2")).toContainText("Dashboard Metrics");
    await expect(page.locator(".stats-value").first()).toContainText("0"); // Total Tasks

    // 3. Create a Task
    // Navigate to tasks page
    await page.click('a[href="/tasks"]');
    await page.waitForURL("**/tasks");
    await expect(page.locator("h2")).toContainText("Task Center");

    // Open Modal
    await page.click("button:has-text('New Task')");
    await expect(page.locator("h3")).toContainText("Create New Task");

    // Fill Task Details
    await page.fill("#taskName", taskName);
    await page.fill("#description", "Created by E2E test script");
    
    // Set Tomorrow's deadline
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dateString = tomorrow.toISOString().slice(0, 16);
    await page.fill("#expectedEndTime", dateString);

    await page.click('button[type="submit"]');
    
    // Wait for modal close and task to show in table
    await page.waitForSelector(`text=${taskName}`);
    await expect(page.locator(".badge-pending")).toBeVisible();

    // 4. Mark Task Complete
    // Click check complete button
    await page.click('button[title="Mark Complete"]');
    await expect(page.locator(".badge-done")).toBeVisible();

    // 5. Verify Dashboard Updates
    await page.click('a[href="/dashboard"]');
    await page.waitForURL("**/dashboard");
    // Verify first stats value is 1 (Total Tasks)
    await expect(page.locator(".stats-value").first()).toContainText("1");
    // Verify second stats value is 1 (Done Tasks)
    await expect(page.locator(".stats-value").nth(1)).toContainText("1");

    // 6. Verify Audit Entry Exists
    await page.click('a[href="/audit"]');
    await page.waitForURL("**/audit");
    await expect(page.locator("h2")).toContainText("Audit Trails");
    
    // Verify audits for login, task_create, task_update are recorded
    await expect(page.locator("text=login").first()).toBeVisible();
    await expect(page.locator("text=task_create").first()).toBeVisible();
    await expect(page.locator("text=task_update").first()).toBeVisible();
  });
});
