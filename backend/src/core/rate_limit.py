import os

from slowapi import Limiter
from slowapi.util import get_remote_address

from src.core.config import settings


enabled = (
    os.getenv("TESTING", "").lower() != "true"
    and os.getenv("DISABLE_RATE_LIMIT", "").lower() != "true"
    and os.getenv("PERFORMANCE_TEST", "").lower() != "true"
)

limiter = Limiter(
    key_func=get_remote_address,
    enabled=enabled,
    storage_uri=settings.REDIS_URL,
)
