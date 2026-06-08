import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_auth_api_flow(client: AsyncClient):
    """Test standard signup, login, get-profile, token-refresh, and logout HTTP flow."""
    username = "integration_user"
    password = "Password123!"

    # 1. Signup Request
    signup_res = await client.post(
        "/api/v1/auth/signup",
        json={"username": username, "password": password, "confirm_password": password},
    )
    assert signup_res.status_code == 201
    assert signup_res.json()["success"] is True

    # 2. Login Request
    login_res = await client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    assert login_res.status_code == 200
    assert login_res.json()["success"] is True

    # Assert Cookies are present in the response
    assert "access_token" in login_res.cookies
    assert "refresh_token" in login_res.cookies

    # 3. Get Current User Profile (me)
    # The client automatically holds the cookies from the login response!
    me_res = await client.get("/api/v1/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["data"]["username"] == username

    # 4. Refresh Session
    refresh_res = await client.post("/api/v1/auth/refresh")
    assert refresh_res.status_code == 200
    assert refresh_res.json()["success"] is True
    assert "access_token" in refresh_res.cookies

    # 5. Logout User
    logout_res = await client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200
    assert logout_res.json()["success"] is True

    # Assert cookies are removed (expired/deleted in headers)
    # In HTTPX client, cookies dict should be cleared or contain empty values
    assert client.cookies.get("access_token") is None
