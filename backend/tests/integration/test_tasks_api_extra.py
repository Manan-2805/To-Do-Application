import datetime
import io
import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_tasks_api_validation_errors(client: AsyncClient):
    """Test task creation validation rules."""
    username = "task_validation_u"
    password = "Password123!"
    await client.post(
        "/api/v1/auth/signup",
        json={"username": username, "password": password, "confirm_password": password},
    )
    await client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )

    # 1. Invalid past expected_end_time
    yesterday = (
        datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=1)
    ).isoformat()
    response = await client.post(
        "/api/v1/tasks/",
        data={
            "task_name": "Past Task",
            "description": "Invalid time",
            "expected_end_time": yesterday,
        },
    )
    assert response.status_code == 400

    # 2. Blank task name
    tomorrow = (
        datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
    ).isoformat()
    response = await client.post(
        "/api/v1/tasks/",
        data={
            "task_name": "",
            "description": "Blank name",
            "expected_end_time": tomorrow,
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_tasks_api_queries_and_filters(client: AsyncClient):
    """Test task retrieval with search filters and pagination limits."""
    username = "task_queries_u"
    password = "Password123!"
    await client.post(
        "/api/v1/auth/signup",
        json={"username": username, "password": password, "confirm_password": password},
    )
    await client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )

    tomorrow = (
        datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
    ).isoformat()

    # Create Task 1
    await client.post(
        "/api/v1/tasks/",
        data={"task_name": "Apple Task", "expected_end_time": tomorrow},
    )
    # Create Task 2
    await client.post(
        "/api/v1/tasks/",
        data={"task_name": "Banana Task", "expected_end_time": tomorrow},
    )

    # Search: 'Apple'
    search_res = await client.get("/api/v1/tasks/?search=Apple")
    assert search_res.status_code == 200
    assert search_res.json()["data"]["total_count"] == 1
    assert search_res.json()["data"]["tasks"][0]["task_name"] == "Apple Task"

    # Pagination: limit=1
    pag_res = await client.get("/api/v1/tasks/?limit=1")
    assert pag_res.status_code == 200
    assert len(pag_res.json()["data"]["tasks"]) == 1
    assert pag_res.json()["data"]["total_count"] == 2


@pytest.mark.asyncio
async def test_tasks_api_attachment_upload(client: AsyncClient):
    """Test task creation and updating with a multipart file attachment."""
    username = "task_attachment_u"
    password = "Password123!"
    await client.post(
        "/api/v1/auth/signup",
        json={"username": username, "password": password, "confirm_password": password},
    )
    await client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )

    tomorrow = (
        datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)
    ).isoformat()

    # Create with attachment
    file_data = {
        "attachment": ("test_image.png", io.BytesIO(b"dummy_image_data"), "image/png")
    }
    form_data = {
        "task_name": "Attachment Task",
        "expected_end_time": tomorrow,
    }

    create_res = await client.post("/api/v1/tasks/", data=form_data, files=file_data)
    assert create_res.status_code == 201
    assert create_res.json()["data"]["attachment_path"] is not None

    task_id = create_res.json()["data"]["id"]

    # Update attachment
    new_file_data = {
        "attachment": ("new_image.png", io.BytesIO(b"new_dummy_data"), "image/png")
    }
    update_res = await client.put(
        f"/api/v1/tasks/{task_id}", data={}, files=new_file_data
    )
    assert update_res.status_code == 200
    assert "new_image.png" in update_res.json()["data"]["attachment_path"]


@pytest.mark.asyncio
async def test_tasks_api_delete_non_existent(client: AsyncClient):
    """Test deleting a non-existent task returns 404."""
    username = "task_del_u"
    password = "Password123!"
    await client.post(
        "/api/v1/auth/signup",
        json={"username": username, "password": password, "confirm_password": password},
    )
    await client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )

    random_id = uuid.uuid4()
    response = await client.delete(f"/api/v1/tasks/{random_id}")
    assert response.status_code == 404
