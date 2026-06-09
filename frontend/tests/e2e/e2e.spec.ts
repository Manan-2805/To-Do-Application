import { expect, test } from "@playwright/test";

test.describe("TodoSphere End-to-End Flow", () => {
  const username = `e2e_user_${Date.now()}`;
  const password = "Password123!";
  const taskName1 = `E2E Task A_${Date.now()}`;
  const taskName2 = `E2E Task B_${Date.now()}`;
  const taskName3 = `E2E Task C_${Date.now()}`;

  test("User lifecycle: signup, login, multi-task management, dashboard, audit, theme toggle, and logout", async ({
    page,
  }) => {
    page.on("console", (msg) => {
      const text = msg.text();
      if (text.includes("Failed to load resource") && text.includes("401")) {
        return;
      }
      console.log("BROWSER CONSOLE:", text);
    });

    page.on("response", async (response) => {
      const url = response.url();
      const status = response.status();
      if (status >= 400) {
        if (
          status === 401 &&
          (url.includes("/api/v1/auth/me") || url.includes("/api/v1/auth/refresh"))
        ) {
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

    // 3. Create 3 Tasks
    // Navigate to tasks page
    await page.click('a[href="/tasks"]');
    await page.waitForURL("**/tasks");
    await expect(page.locator("h2")).toContainText("Task Center");

    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dateString = tomorrow.toISOString().slice(0, 16);

    // Create Task A
    await page.click("button:has-text('New Task')");
    await expect(page.locator("h3")).toContainText("Create New Task");
    await page.fill("#taskName", taskName1);
    await page.fill("#description", "First test task");
    await page.fill("#expectedEndTime", dateString);
    await page.click('button[type="submit"]');
    await page.waitForSelector(`text=${taskName1}`);

    // Create Task B
    await page.click("button:has-text('New Task')");
    await expect(page.locator("h3")).toContainText("Create New Task");
    await page.fill("#taskName", taskName2);
    await page.fill("#description", "Second test task");
    await page.fill("#expectedEndTime", dateString);
    await page.click('button[type="submit"]');
    await page.waitForSelector(`text=${taskName2}`);

    // Create Task C
    await page.click("button:has-text('New Task')");
    await expect(page.locator("h3")).toContainText("Create New Task");
    await page.fill("#taskName", taskName3);
    await page.fill("#description", "Third test task");
    await page.fill("#expectedEndTime", dateString);
    await page.click('button[type="submit"]');
    await page.waitForSelector(`text=${taskName3}`);

    // 4. Change Status of Task B (Mark it Complete)
    const row = page.locator("tr", { hasText: taskName2 });
    await row.locator('button[title="Mark Complete"]').click();
    await expect(row.locator(".badge-done")).toBeVisible();

    // 5. Verify Dashboard Updates
    await page.click('a[href="/dashboard"]');
    await page.waitForURL("**/dashboard");
    // Verify first stats value is 3 (Total Tasks)
    await expect(page.locator(".stats-value").first()).toContainText("3");
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

    // 7. Toggle Theme
    const initialTheme = await page.evaluate(() => document.body.classList.contains("dark"));
    await page.click('button[aria-label="Toggle theme"]');

    const toggledTheme = await page.evaluate(() => document.body.classList.contains("dark"));
    expect(toggledTheme).not.toBe(initialTheme);

    await page.click('button[aria-label="Toggle theme"]');
    const resetTheme = await page.evaluate(() => document.body.classList.contains("dark"));
    expect(resetTheme).toBe(initialTheme);

    // 8. Mandatory Logout
    await page.click('button[aria-label="Logout"]');
    await page.waitForURL("**/login");

    // Verify redirect when attempting to access authenticated pages
    await page.goto("/dashboard");
    await page.waitForURL("**/login");
  });
});
