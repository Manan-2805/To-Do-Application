import datetime
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from src.core.redis_cache import (
    get_cached_response,
    get_redis_client,
    invalidate_user_cache,
    json_serializable_fallback,
    set_cached_response,
)


@pytest.mark.asyncio
async def test_redis_cache_get_set() -> None:
    """Verify that cached data is properly retrieved and stored."""
    mock_client = AsyncMock()
    mock_client.get.return_value = '{"foo": "bar"}'

    with patch("src.core.redis_cache.get_redis_client", return_value=mock_client):
        # Test Get
        res = await get_cached_response("test_key")
        assert res == {"foo": "bar"}
        mock_client.get.assert_called_once_with("test_key")

        # Test Set
        await set_cached_response("test_key", {"a": 1}, expire_seconds=60)
        mock_client.set.assert_called_once_with("test_key", '{"a": 1}', ex=60)


@pytest.mark.asyncio
async def test_redis_cache_get_exception() -> None:
    """Verify that get exception is caught and returns None."""
    mock_client = AsyncMock()
    mock_client.get.side_effect = Exception("Redis connection error")

    with patch("src.core.redis_cache.get_redis_client", return_value=mock_client):
        res = await get_cached_response("test_key")
        assert res is None


@pytest.mark.asyncio
async def test_redis_cache_set_exception() -> None:
    """Verify that set exception is caught and handled."""
    mock_client = AsyncMock()
    mock_client.set.side_effect = Exception("Redis write error")

    with patch("src.core.redis_cache.get_redis_client", return_value=mock_client):
        # Should catch exception and not crash
        await set_cached_response("test_key", {"a": 1})


@pytest.mark.asyncio
async def test_redis_cache_invalidate() -> None:
    """Verify that cache invalidation deletes keys matching user prefix."""
    mock_client = AsyncMock()
    mock_client.keys.return_value = ["user:1:key1", "user:1:key2"]

    with patch("src.core.redis_cache.get_redis_client", return_value=mock_client):
        await invalidate_user_cache(1)
        mock_client.keys.assert_called_once_with("user:1:*")
        mock_client.delete.assert_called_once_with("user:1:key1", "user:1:key2")


@pytest.mark.asyncio
async def test_redis_cache_invalidate_no_keys() -> None:
    """Verify cache invalidation proceeds correctly if no matching keys are found."""
    mock_client = AsyncMock()
    mock_client.keys.return_value = []

    with patch("src.core.redis_cache.get_redis_client", return_value=mock_client):
        await invalidate_user_cache(1)
        mock_client.keys.assert_called_once_with("user:1:*")
        mock_client.delete.assert_not_called()


@pytest.mark.asyncio
async def test_redis_cache_invalidate_exception() -> None:
    """Verify that invalidation exception is caught and handled."""
    mock_client = AsyncMock()
    mock_client.keys.side_effect = Exception("Redis query error")

    with patch("src.core.redis_cache.get_redis_client", return_value=mock_client):
        # Should catch exception and not crash
        await invalidate_user_cache(1)


def test_get_redis_client() -> None:
    """Verify get_redis_client initializes client successfully."""
    client = get_redis_client()
    assert client is not None


def test_json_serializable_fallback() -> None:
    """Verify JSON serialization fallback helper behavior for various types."""
    # 1. Test UUID
    u = uuid.uuid4()
    assert json_serializable_fallback(u) == str(u)

    # 2. Test datetime
    dt = datetime.datetime(2026, 6, 8, 12, 0, 0)
    assert json_serializable_fallback(dt) == dt.isoformat()

    # 3. Test date
    d = datetime.date(2026, 6, 8)
    assert json_serializable_fallback(d) == d.isoformat()

    # 4. Test TypeError for unsupported type
    with pytest.raises(TypeError):
        json_serializable_fallback(object())
