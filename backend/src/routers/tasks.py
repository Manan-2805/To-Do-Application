import datetime
import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging_conf import correlation_id_ctx
from src.core.rate_limit import limiter
from src.core.redis_cache import (
    get_cached_response,
    invalidate_user_cache,
    set_cached_response,
)
from src.dependencies.auth import get_current_user
from src.dependencies.database import get_db_session
from src.dependencies.pagination import PaginationParams
from src.models.task import TaskStatus
from src.models.user import User
from src.schemas.response import APIResponse
from src.schemas.task import (
    DashboardStatsResponse,
    PaginatedTasksResponse,
    TaskResponse,
)
from src.services.task import TaskService
from src.utils.export import export_tasks_to_excel, export_tasks_to_pdf


router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/", response_model=APIResponse[TaskResponse], status_code=201)
@limiter.limit("20/minute")
async def create_task(
    request: Request,  # noqa: ARG001
    task_name: str = Form(..., min_length=1, max_length=255),
    description: str | None = Form(None, max_length=1000),
    expected_end_time: datetime.datetime = Form(...),
    attachment: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[TaskResponse]:
    """Create a new task with optional file attachment under rate limit controls."""
    task_service = TaskService(db)

    attachment_bytes = None
    attachment_name = None
    if attachment:
        attachment_bytes = await attachment.read()
        attachment_name = attachment.filename

    task = await task_service.create_task(
        user_id=current_user.id,
        task_name=task_name,
        description=description,
        expected_end_time=expected_end_time,
        attachment_name=attachment_name,
        attachment_bytes=attachment_bytes,
    )

    await invalidate_user_cache(current_user.id)

    task_data = TaskResponse.model_validate(task)
    return APIResponse(
        success=True,
        data=task_data,
        error=None,
        correlation_id=correlation_id_ctx.get(),
    )


@router.get("/", response_model=APIResponse[PaginatedTasksResponse])
async def list_tasks(
    status: TaskStatus | None = Query(None),
    search: str | None = Query(None),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[PaginatedTasksResponse]:
    """Query tasks for user applying status filter, name search, sorting, and pagination."""
    cache_key = (
        f"user:{current_user.id}:tasks:list:"
        f"status={status or 'None'}:"
        f"search={search or 'None'}:"
        f"offset={pagination.offset}:"
        f"limit={pagination.limit}:"
        f"sort_by={pagination.sort_by}:"
        f"sort_order={pagination.sort_order}"
    )
    cached = await get_cached_response(cache_key)
    if cached:
        cached["correlation_id"] = correlation_id_ctx.get()
        return APIResponse[PaginatedTasksResponse](**cached)

    task_service = TaskService(db)
    tasks, total_count = await task_service.get_tasks(
        user_id=current_user.id,
        status=status,
        search=search,
        offset=pagination.offset,
        limit=pagination.limit,
        sort_by=pagination.sort_by,
        sort_order=pagination.sort_order,
    )

    task_list = [TaskResponse.model_validate(t) for t in tasks]
    data = PaginatedTasksResponse(
        tasks=task_list,
        total_count=total_count,
        page=pagination.page,
        limit=pagination.limit,
    )

    res: APIResponse[PaginatedTasksResponse] = APIResponse(
        success=True, data=data, error=None, correlation_id=correlation_id_ctx.get()
    )
    await set_cached_response(
        cache_key, res.model_dump(mode="json"), expire_seconds=300
    )
    return res


@router.get("/stats", response_model=APIResponse[DashboardStatsResponse])
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[DashboardStatsResponse]:
    """Fetch task counts grouped by status for dashboard summary cards and pie charts."""
    cache_key = f"user:{current_user.id}:tasks:stats"
    cached = await get_cached_response(cache_key)
    if cached:
        cached["correlation_id"] = correlation_id_ctx.get()
        return APIResponse[DashboardStatsResponse](**cached)

    task_service = TaskService(db)
    counts = await task_service.get_status_counts(current_user.id)
    total = sum(counts.values())

    data = DashboardStatsResponse(counts=counts, total=total)
    res: APIResponse[DashboardStatsResponse] = APIResponse(
        success=True, data=data, error=None, correlation_id=correlation_id_ctx.get()
    )
    await set_cached_response(
        cache_key, res.model_dump(mode="json"), expire_seconds=300
    )
    return res


@router.get("/export/excel")
@limiter.limit("10/minute")
async def export_excel(
    request: Request,  # noqa: ARG001
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    """Generate and stream task list as an Excel file document."""
    task_service = TaskService(db)
    # Get all active tasks for user (no pagination)
    tasks, _ = await task_service.get_tasks(user_id=current_user.id, limit=10000)

    excel_stream = export_tasks_to_excel(tasks)

    # Log Audit
    await task_service.audit_service.log_action(
        user_id=current_user.id,
        action="export",
        entity_type="task",
        metadata={"export_type": "excel"},
    )
    await db.commit()

    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=todosphere_tasks.xlsx"},
    )


@router.get("/export/pdf")
@limiter.limit("10/minute")
async def export_pdf(
    request: Request,  # noqa: ARG001
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    """Generate and stream task list as a PDF report."""
    task_service = TaskService(db)
    tasks, _ = await task_service.get_tasks(user_id=current_user.id, limit=10000)

    pdf_stream = export_tasks_to_pdf(tasks)

    # Log Audit
    await task_service.audit_service.log_action(
        user_id=current_user.id,
        action="export",
        entity_type="task",
        metadata={"export_type": "pdf"},
    )
    await db.commit()

    return StreamingResponse(
        pdf_stream,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=todosphere_tasks.pdf"},
    )


@router.get("/{task_id}", response_model=APIResponse[TaskResponse])
async def get_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[TaskResponse]:
    """Fetch details of a specific task."""
    cache_key = f"user:{current_user.id}:tasks:detail:{task_id}"
    cached = await get_cached_response(cache_key)
    if cached:
        cached["correlation_id"] = correlation_id_ctx.get()
        return APIResponse[TaskResponse](**cached)

    task_service = TaskService(db)
    task = await task_service.get_task_by_id(task_id, current_user.id)

    task_data = TaskResponse.model_validate(task)
    res: APIResponse[TaskResponse] = APIResponse(
        success=True,
        data=task_data,
        error=None,
        correlation_id=correlation_id_ctx.get(),
    )
    await set_cached_response(
        cache_key, res.model_dump(mode="json"), expire_seconds=300
    )
    return res


@router.put("/{task_id}", response_model=APIResponse[TaskResponse])
@limiter.limit("30/minute")
async def update_task(
    request: Request,  # noqa: ARG001
    task_id: uuid.UUID,
    task_name: str | None = Form(None, min_length=1, max_length=255),
    description: str | None = Form(None, max_length=1000),
    status: TaskStatus | None = Form(None),
    expected_end_time: datetime.datetime | None = Form(None),
    attachment: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[TaskResponse]:
    """Update task fields, status transitions, and attachment uploads."""
    task_service = TaskService(db)

    attachment_bytes = None
    attachment_name = None
    if attachment:
        attachment_bytes = await attachment.read()
        attachment_name = attachment.filename

    task = await task_service.update_task(
        task_id=task_id,
        user_id=current_user.id,
        task_name=task_name,
        description=description,
        status=status,
        expected_end_time=expected_end_time,
        attachment_name=attachment_name,
        attachment_bytes=attachment_bytes,
    )

    await invalidate_user_cache(current_user.id)

    task_data = TaskResponse.model_validate(task)
    return APIResponse(
        success=True,
        data=task_data,
        error=None,
        correlation_id=correlation_id_ctx.get(),
    )


@router.delete("/{task_id}", response_model=APIResponse[dict[str, Any]])
@limiter.limit("20/minute")
async def delete_task(
    request: Request,  # noqa: ARG001
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[dict[str, Any]]:
    """Soft-delete task from dashboard lists."""
    task_service = TaskService(db)
    await task_service.soft_delete_task(task_id, current_user.id)

    await invalidate_user_cache(current_user.id)

    return APIResponse(
        success=True,
        data={"message": "Task deleted successfully"},
        error=None,
        correlation_id=correlation_id_ctx.get(),
    )
