import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_auth_api_signup_validation_failure(client: AsyncClient):
    """Test signup fails when username is too short."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "username": "a",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False


@pytest.mark.asyncio
async def test_auth_api_login_invalid_credentials(client: AsyncClient):
    """Test login fails with invalid password."""
    await client.post(
        "/api/v1/auth/signup",
        json={
            "username": "extra_login_u",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "extra_login_u", "password": "WrongPassword123!"},
    )
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False


@pytest.mark.asyncio
async def test_auth_api_me_unauthenticated(client: AsyncClient):
    """Test get-profile /me returns 401 when not logged in."""
    async with AsyncClient(
        transport=client._transport, base_url=client.base_url
    ) as anon_client:
        response = await anon_client.get("/api/v1/auth/me")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_api_refresh_missing_cookie(client: AsyncClient):
    """Test token refresh returns 401 when refresh_token cookie is missing."""
    async with AsyncClient(
        transport=client._transport, base_url=client.base_url
    ) as anon_client:
        response = await anon_client.post("/api/v1/auth/refresh")
        assert response.status_code == 401
