import logging
from typing import Any

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.logging_conf import correlation_id_ctx
from src.core.redis_cache import get_redis_client
from src.dependencies.database import get_db_session
from src.schemas.response import APIResponse, ErrorDetail
from src.services.storage import get_storage_provider


logger = logging.getLogger("todosphere.health")
router = APIRouter(tags=["Health"])


@router.get("/health/live", response_model=APIResponse[dict[str, Any]])
async def liveness_check() -> APIResponse[dict[str, Any]]:
    """Liveness check returning instantly to verify the HTTP server is running."""
    return APIResponse(
        success=True,
        data={"status": "alive"},
        error=None,
        correlation_id=correlation_id_ctx.get(),
    )


@router.get("/health/ready")
async def readiness_check(
    response: Response, db: AsyncSession = Depends(get_db_session)
) -> APIResponse[dict[str, Any]]:
    """Readiness check verifying database connectivity, cache server, and storage permissions."""
    db_ok = False
    redis_ok = False
    storage_ok = False

    # 1. Check PostgreSQL Database
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error(f"Readiness check failed: database unreachable: {e!s}")

    # 2. Check Redis Cache
    try:
        redis_client = get_redis_client()
        await redis_client.ping()
        redis_ok = True
    except Exception as e:
        logger.error(f"Readiness check failed: Redis unreachable: {e!s}")

    # 3. Check Attachment Storage
    try:
        storage_provider = get_storage_provider()
        storage_ok = await storage_provider.check_health()
    except Exception as e:
        logger.error(f"Readiness check failed: Storage provider unhealthy: {e!s}")

    ready = db_ok and redis_ok and storage_ok
    status_code = 200 if ready else 503
    response.status_code = status_code

    data = {
        "postgres": "healthy" if db_ok else "unhealthy",
        "redis": "healthy" if redis_ok else "unhealthy",
        "storage": "healthy" if storage_ok else "unhealthy",
    }

    if ready:
        return APIResponse(
            success=True, data=data, error=None, correlation_id=correlation_id_ctx.get()
        )
    return APIResponse(
        success=False,
        data=data,
        error=ErrorDetail(
            code="SERVICE_UNAVAILABLE",
            message="One or more background services are unreachable or unhealthy.",
        ),
        correlation_id=correlation_id_ctx.get(),
    )
