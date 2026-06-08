from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging_conf import correlation_id_ctx
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
):
    """Retrieve audit history log for the current authenticated user session."""
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

    return APIResponse(
        success=True, data=data, error=None, correlation_id=correlation_id_ctx.get()
    )
