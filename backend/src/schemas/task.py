import datetime
import uuid

from pydantic import BaseModel, Field

from src.models.task import TaskStatus


class TaskCreateRequest(BaseModel):
    task_name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the task"
    )
    description: str | None = Field(
        None, max_length=1000, description="Detailed description"
    )
    expected_end_time: datetime.datetime = Field(
        ..., description="Expected deadline date/time"
    )


class TaskUpdateRequest(BaseModel):
    task_name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    status: TaskStatus | None = Field(None)
    expected_end_time: datetime.datetime | None = Field(None)


class TaskResponse(BaseModel):
    id: uuid.UUID
    task_name: str
    description: str | None = None
    status: TaskStatus
    start_time: datetime.datetime
    expected_end_time: datetime.datetime
    actual_end_time: datetime.datetime | None = None
    attachment_path: str | None = None
    total_time_taken_seconds: int | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True
        json_encoders = {datetime.datetime: lambda dt: dt.isoformat()}  # noqa: RUF012


class PaginatedTasksResponse(BaseModel):
    tasks: list[TaskResponse]
    total_count: int
    page: int
    limit: int


class DashboardStatsResponse(BaseModel):
    counts: dict[str, int] = Field(..., description="Task counts by status")
    total: int = Field(..., description="Total non-deleted tasks")
