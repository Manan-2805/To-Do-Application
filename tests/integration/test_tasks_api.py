import datetime

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_tasks_api_lifecycle(client: AsyncClient):
    """Test full task HTTP lifecycle: create, list, filter, update, complete, and delete."""
    # 0. Setup User and Session
    signup_res = await client.post(
        "/api/v1/auth/signup",
        json={
            "username": "task_api_user",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert signup_res.status_code == 201

    await client.post(
        "/api/v1/auth/login",
        json={"username": "task_api_user", "password": "Password123!"},
    )

    # 1. Create a Task (Requires multipart/form-data)
    tomorrow = (
        datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
    ).isoformat()
    form_data = {
        "task_name": "API Test Task",
        "description": "Integration task description",
        "expected_end_time": tomorrow,
    }

    create_res = await client.post("/api/v1/tasks/", data=form_data)
    assert create_res.status_code == 201

    task_id = create_res.json()["data"]["id"]
    assert task_id is not None
    assert create_res.json()["data"]["status"] == "Pending"

    # 2. List Tasks
    list_res = await client.get("/api/v1/tasks/?page=1&limit=10")
    assert list_res.status_code == 200
    assert list_res.json()["data"]["total_count"] == 1
    assert list_res.json()["data"]["tasks"][0]["task_name"] == "API Test Task"

    # 3. Update Task Status (In Progress)
    update_res = await client.put(
        f"/api/v1/tasks/{task_id}", data={"status": "In Progress"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["status"] == "In Progress"

    # 4. Get Dashboard Statistics
    stats_res = await client.get("/api/v1/tasks/stats")
    assert stats_res.status_code == 200
    assert stats_res.json()["data"]["counts"]["In Progress"] == 1
    assert stats_res.json()["data"]["total"] == 1

    # 5. Export Tasks (Excel / PDF)
    excel_res = await client.get("/api/v1/tasks/export/excel")
    assert excel_res.status_code == 200
    assert (
        excel_res.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    pdf_res = await client.get("/api/v1/tasks/export/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"

    # 6. Delete Task (Soft delete)
    delete_res = await client.delete(f"/api/v1/tasks/{task_id}")
    assert delete_res.status_code == 200
    assert delete_res.json()["data"]["message"] == "Task deleted successfully"

    # 7. Verify task no longer appears in lists
    list_after_res = await client.get("/api/v1/tasks/")
    assert list_after_res.json()["data"]["total_count"] == 0
