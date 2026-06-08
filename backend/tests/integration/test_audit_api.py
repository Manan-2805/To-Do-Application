import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_audit_api_flow(client: AsyncClient):
    """Test retrieving audit logs via API with sorting and pagination."""
    username = "audit_test_u"
    password = "Password123!"

    # Signup
    await client.post(
        "/api/v1/auth/signup",
        json={"username": username, "password": password, "confirm_password": password},
    )
    # Login to authenticate client session (cookies)
    await client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )

    # Fetch audits (should contain signup & login events)
    response = await client.get("/api/v1/audit/")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["total_count"] >= 2
    assert len(body["data"]["audits"]) >= 2

    # Fetch with pagination parameters
    pag_response = await client.get("/api/v1/audit/?limit=1&sort_order=asc")
    assert pag_response.status_code == 200
    pag_body = pag_response.json()
    assert pag_body["success"] is True
    assert pag_body["data"]["limit"] == 1
    assert len(pag_body["data"]["audits"]) == 1
