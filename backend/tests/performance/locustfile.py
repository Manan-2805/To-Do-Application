import datetime
import logging
import random
import time

from locust import HttpUser, between, task


logger = logging.getLogger("locust.test")


class TodoSphereLoadTestUser(HttpUser):
    """Locust user simulating signups, login, task flows, dashboard views, and audit log retrievals."""

    wait_time = between(1, 3)

    def on_start(self) -> None:
        """Onboard user by registering and establishing active cookies session."""
        self.username = f"locust_{int(time.time())}_{random.randint(1000, 9999)}"
        self.password = "Password123!"
        self.task_ids: list[str] = []
        self.authenticated = False

        # 1. Signup
        with self.client.post(
            "/api/v1/auth/signup",
            json={
                "username": self.username,
                "password": self.password,
                "confirm_password": self.password,
            },
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                try:
                    body = response.json()
                    if body.get("success"):
                        response.success()
                    else:
                        response.failure(
                            f"Signup succeeded HTTP-wise but API success is False: {body.get('error')}"
                        )
                except Exception as e:
                    response.failure(f"Failed to parse signup response: {e!s}")
            else:
                response.failure(
                    f"Signup failed with status code {response.status_code}: {response.text}"
                )

        # 2. Login (stores HttpOnly cookies in Locust Session)
        with self.client.post(
            "/api/v1/auth/login",
            json={"username": self.username, "password": self.password},
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                try:
                    body = response.json()
                    if body.get("success"):
                        self.authenticated = True
                        response.success()
                    else:
                        response.failure(
                            f"Login response success is False: {body.get('error')}"
                        )
                except Exception as e:
                    response.failure(f"Failed to parse login response: {e!s}")
            else:
                response.failure(
                    f"Login failed with status code {response.status_code}: {response.text}"
                )

    @task(3)
    def fetch_dashboard_and_audit(self) -> None:
        """Simulate fetching dashboard stats and auditing activity data."""
        if not self.authenticated:
            return

        with self.client.get("/api/v1/tasks/stats", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Fetch stats failed: {response.status_code} - {response.text}"
                )

        with self.client.get("/api/v1/audit/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Fetch audits failed: {response.status_code} - {response.text}"
                )

    @task(4)
    def list_and_search_tasks(self) -> None:
        """Simulate listing tasks with queries."""
        if not self.authenticated:
            return

        with self.client.get(
            "/api/v1/tasks/?page=1&limit=10", catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"List tasks failed: {response.status_code} - {response.text}"
                )

        with self.client.get(
            "/api/v1/tasks/?search=Locust&page=1&limit=10", catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Search tasks failed: {response.status_code} - {response.text}"
                )

    @task(2)
    def task_lifecycle(self) -> None:
        """Perform creation, progression, and completion of tasks."""
        if not self.authenticated:
            return

        # Create Task (form-data format)
        deadline = (
            datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
        ).isoformat()
        payload = {
            "task_name": f"Locust Task {random.randint(100, 999)}",
            "description": "Locust automated performance task",
            "expected_end_time": deadline,
        }

        task_id = None
        with self.client.post(
            "/api/v1/tasks/", data=payload, catch_response=True
        ) as response:
            if response.status_code == 201:
                try:
                    body = response.json()
                    if body.get("success") and body.get("data"):
                        task_id = body["data"]["id"]
                        self.task_ids.append(task_id)
                        response.success()
                    else:
                        response.failure(
                            f"Create task API success is False: {body.get('error')}"
                        )
                except Exception as e:
                    response.failure(f"Failed to parse create task response: {e!s}")
            else:
                response.failure(
                    f"Create task failed with status {response.status_code}: {response.text}"
                )

        # Proceed and finish a task if list is not empty
        if self.task_ids:
            active_id = self.task_ids[0]

            # Start
            with self.client.put(
                f"/api/v1/tasks/{active_id}",
                name="/api/v1/tasks/[id]",
                data={"status": "In Progress"},
                catch_response=True,
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(
                        f"Update task to In Progress failed: {response.status_code} - {response.text}"
                    )

            # Complete
            with self.client.put(
                f"/api/v1/tasks/{active_id}",
                name="/api/v1/tasks/[id]",
                data={"status": "Done"},
                catch_response=True,
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(
                        f"Update task to Done failed: {response.status_code} - {response.text}"
                    )

            self.task_ids.pop(0)
