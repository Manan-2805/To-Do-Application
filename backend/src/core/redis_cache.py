import datetime
import json
import logging
import uuid
from typing import Any

from redis.asyncio import Redis, from_url

from src.core.config import settings


logger = logging.getLogger("todosphere.cache")

redis_client: Redis | None = None


def json_serializable_fallback(obj: Any) -> str:
    """Fallback serialization for UUID and datetime objects."""
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def get_redis_client() -> Redis:
    """Retrieve or initialize the async Redis client."""
    global redis_client
    if redis_client is None:
        redis_client = from_url(settings.REDIS_URL, decode_responses=True)
    return redis_client


async def get_cached_response(key: str) -> Any | None:
    """Retrieve JSON-deserialized value from cache."""
    try:
        client = get_redis_client()
        data = await client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        logger.warning(f"Cache read error for key {key}: {e!s}")
    return None


async def set_cached_response(key: str, data: Any, expire_seconds: int = 300) -> None:
    """Serialize and write value to cache with TTL, tracking user keys in a Set."""
    try:
        client = get_redis_client()
        serialized = json.dumps(data, default=json_serializable_fallback)
        await client.set(key, serialized, ex=expire_seconds)

        parts = key.split(":")
        if len(parts) > 1 and parts[0] == "user":
            user_id = parts[1]
            set_key = f"user:{user_id}:keys"
            await client.sadd(set_key, key)
            await client.expire(set_key, expire_seconds)
    except Exception as e:
        logger.warning(f"Cache write error for key {key}: {e!s}")


async def invalidate_user_cache(user_id: Any) -> None:
    """Invalidate all cached keys for a user using the tracking Set (O(1))."""
    try:
        client = get_redis_client()
        set_key = f"user:{user_id}:keys"
        keys = await client.smembers(set_key)
        if keys:
            await client.delete(*keys)
            await client.delete(set_key)
            logger.info(f"Invalidated {len(keys)} cache keys for user {user_id}")
    except Exception as e:
        logger.warning(f"Cache invalidation error for user {user_id}: {e!s}")
