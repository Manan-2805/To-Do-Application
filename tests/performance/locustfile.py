import datetime
import random
import time

from locust import HttpUser, between, task


class TodoSphereLoadTestUser(HttpUser):
    """Locust user simulating signups, login, task flows, dashboard views, and audit log retrievals."""

    wait_time = between(1, 3)

    def on_start(self):
        """Onboard user by registering and establishing active cookies session."""
        self.username = f"locust_{int(time.time())}_{random.randint(1000, 9999)}"
        self.password = "Password123!"
        self.task_ids = []

        # 1. Signup
        self.client.post(
            "/api/v1/auth/signup",
            json={
                "username": self.username,
                "password": self.password,
                "confirm_password": self.password,
            },
        )

        # 2. Login (stores HttpOnly cookies in Locust Session)
        self.client.post(
            "/api/v1/auth/login",
            json={"username": self.username, "password": self.password},
        )

    @task(3)
    def fetch_dashboard_and_audit(self):
        """Simulate fetching dashboard stats and auditing activity data."""
        self.client.get("/api/v1/tasks/stats")
        self.client.get("/api/v1/audit/")

    @task(4)
    def list_and_search_tasks(self):
        """Simulate listing tasks with queries."""
        self.client.get("/api/v1/tasks/?page=1&limit=10")
        self.client.get("/api/v1/tasks/?search=Locust&page=1&limit=10")

    @task(2)
    def task_lifecycle(self):
        """Perform creation, progression, and completion of tasks."""
        # Create Task (form-data format)
        deadline = (
            datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
        ).isoformat()
        payload = {
            "task_name": f"Locust Task {random.randint(100, 999)}",
            "description": "Locust automated performance task",
            "expected_end_time": deadline,
        }

        response = self.client.post("/api/v1/tasks/", data=payload)
        if response.status_code == 201:
            body = response.json()
            if body.get("success") and body.get("data"):
                task_id = body["data"]["id"]
                self.task_ids.append(task_id)

        # Proceed and finish a task if list is not empty
        if self.task_ids:
            active_id = self.task_ids[0]

            # Start
            self.client.put(
                f"/api/v1/tasks/{active_id}", data={"status": "In Progress"}
            )

            # Complete
            self.client.put(f"/api/v1/tasks/{active_id}", data={"status": "Done"})

            self.task_ids.pop(0)
