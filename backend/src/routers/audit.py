from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging_conf import correlation_id_ctx
from src.core.redis_cache import get_cached_response, set_cached_response
from src.dependencies.auth import get_current_user
from src.dependencies.database import get_db_session
from src.dependencies.pagination import PaginationParams
from src.models.user import User
from src.schemas.audit import AuditResponse, PaginatedAuditResponse
from src.schemas.response import APIResponse
from src.services.audit import AuditService


router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get("/", response_model=APIResponse[PaginatedAuditResponse])
async def list_audits(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[PaginatedAuditResponse]:
    """Retrieve audit history log for the current authenticated user session."""
    cache_key = (
        f"user:{current_user.id}:audits:list:"
        f"offset={pagination.offset}:"
        f"limit={pagination.limit}:"
        f"sort_by={pagination.sort_by}:"
        f"sort_order={pagination.sort_order}"
    )
    cached = await get_cached_response(cache_key)
    if cached:
        cached["correlation_id"] = correlation_id_ctx.get()
        return APIResponse[PaginatedAuditResponse](**cached)

    audit_service = AuditService(db)
    audits, total_count = await audit_service.get_audits(
        user_id=current_user.id,
        offset=pagination.offset,
        limit=pagination.limit,
        sort_by=pagination.sort_by,
        sort_order=pagination.sort_order,
    )

    audit_list = [AuditResponse.model_validate(a) for a in audits]
    data = PaginatedAuditResponse(
        audits=audit_list,
        total_count=total_count,
        page=pagination.page,
        limit=pagination.limit,
    )

    res: APIResponse[PaginatedAuditResponse] = APIResponse(
        success=True, data=data, error=None, correlation_id=correlation_id_ctx.get()
    )
    await set_cached_response(
        cache_key, res.model_dump(mode="json"), expire_seconds=300
    )
    return res
