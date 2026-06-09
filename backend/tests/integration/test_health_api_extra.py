from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_readiness_endpoint_db_failure(
    client: AsyncClient, db_session: AsyncSession
):
    """Test health readiness failure when database connection fails."""
    with patch.object(
        db_session, "execute", side_effect=Exception("Database Connection Refused")
    ):
        response = await client.get("/health/ready")
        assert response.status_code == 503
        body = response.json()
        assert body["success"] is False
        assert body["data"]["postgres"] == "unhealthy"


@pytest.mark.asyncio
async def test_readiness_endpoint_redis_failure(client: AsyncClient):
    """Test health readiness failure when Redis connection fails."""
    with patch("src.routers.health.get_redis_client") as mock_get_redis:
        mock_redis = AsyncMock()
        mock_redis.ping.side_effect = Exception("Redis Connection Refused")
        mock_get_redis.return_value = mock_redis

        response = await client.get("/health/ready")
        assert response.status_code == 503
        body = response.json()
        assert body["success"] is False
        assert body["data"]["redis"] == "unhealthy"


@pytest.mark.asyncio
async def test_readiness_endpoint_storage_failure(client: AsyncClient):
    """Test health readiness failure when Storage provider check fails."""
    with patch("src.routers.health.get_storage_provider") as mock_get_storage:
        mock_storage = AsyncMock()
        mock_storage.check_health.return_value = False
        mock_get_storage.return_value = mock_storage

        response = await client.get("/health/ready")
        assert response.status_code == 503
        body = response.json()
        assert body["success"] is False
        assert body["data"]["storage"] == "unhealthy"
