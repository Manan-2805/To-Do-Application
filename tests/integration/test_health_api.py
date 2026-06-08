import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_liveness_endpoint(client: AsyncClient):
    """Test the liveness check returns 200 OK and status is alive."""
    response = await client.get("/health/live")
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "alive"


@pytest.mark.asyncio
async def test_readiness_endpoint(client: AsyncClient):
    """Test the readiness check returns 200 OK because test DB, Redis, and local storage are available."""
    response = await client.get("/health/ready")
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert body["data"]["postgres"] == "healthy"
    assert body["data"]["redis"] == "healthy"
    assert body["data"]["storage"] == "healthy"
