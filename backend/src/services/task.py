import contextlib
import datetime
import os
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import BadRequestException, EntityNotFoundException
from src.models.task import Task, TaskStatus
from src.repositories.task import TaskRepository
from src.services.audit import AuditService
from src.services.storage import get_storage_provider


class TaskService:
    """Service layer managing task lifecycle, state machine transitions, and file attachments."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = TaskRepository(session)
        self.audit_service = AuditService(session)
        self.storage_provider = get_storage_provider()

    def _validate_attachment(self, file_name: str, contents: bytes) -> None:
        """Enforce strict attachment file format and size limits (5 MB)."""
        # 1. Format validation
        allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        _, ext = os.path.splitext(file_name.lower())
        if ext not in allowed_extensions:
            raise BadRequestException(
                f"Invalid file format '{ext}'. Allowed: {', '.join(allowed_extensions)}"
            )

        # 2. Size validation (5 MB limit)
        max_size = 5 * 1024 * 1024
        if len(contents) > max_size:
            raise BadRequestException("Attachment exceeds maximum limit of 5 MB.")

    def _verify_state_transition(self, current: TaskStatus, target: TaskStatus) -> None:
        """Enforce task state machine transition rules."""
        if current == target:
            return

        if current == TaskStatus.DONE:
            raise BadRequestException("Task is in Done state and cannot be modified.")

        valid_transitions = {
            TaskStatus.PENDING: {TaskStatus.IN_PROGRESS, TaskStatus.MISSED},
            TaskStatus.IN_PROGRESS: {TaskStatus.DONE, TaskStatus.MISSED},
            TaskStatus.MISSED: {TaskStatus.IN_PROGRESS},
        }

        if target not in valid_transitions.get(current, set()):
            raise BadRequestException(
                f"Invalid status transition from {current.value} to {target.value}."
            )

    async def get_tasks(
        self,
        user_id: uuid.UUID,
        status: TaskStatus | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 10,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Task], int]:
        """Retrieve tasks for user with filters and sorting."""
        return await self.repository.get_tasks_for_user(
            user_id=user_id,
            status=status,
            search=search,
            offset=offset,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def get_task_by_id(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Task:
        """Fetch task checking ownership."""
        task = await self.repository.get_by_id_for_user(task_id, user_id)
        if not task:
            raise EntityNotFoundException("Task not found.")
        return task

    async def create_task(
        self,
        user_id: uuid.UUID,
        task_name: str,
        description: str | None,
        expected_end_time: datetime.datetime,
        attachment_name: str | None = None,
        attachment_bytes: bytes | None = None,
    ) -> Task:
        """Create a new task, executing validations and uploads."""
        now = datetime.datetime.now(datetime.UTC)

        # Verify times
        if expected_end_time.tzinfo is None:
            expected_end_time = expected_end_time.replace(tzinfo=datetime.UTC)

        if expected_end_time < now:
            raise BadRequestException("Expected end time cannot be in the past.")

        attachment_path = None
        if attachment_name and attachment_bytes:
            self._validate_attachment(attachment_name, attachment_bytes)
            attachment_path = await self.storage_provider.save_file(
                attachment_name, attachment_bytes
            )

        new_task = Task(
            user_id=user_id,
            task_name=task_name,
            description=description,
            status=TaskStatus.PENDING,
            start_time=now,
            expected_end_time=expected_end_time,
            attachment_path=attachment_path,
        )

        await self.repository.create(new_task)

        # Log Audit
        await self.audit_service.log_action(
            user_id=user_id,
            action="task_create",
            entity_type="task",
            entity_id=str(new_task.id),
            metadata={"task_name": task_name},
        )

        await self.session.commit()
        await self.session.refresh(new_task)
        return new_task

    async def update_task(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        task_name: str | None = None,
        description: str | None = None,
        status: TaskStatus | None = None,
        expected_end_time: datetime.datetime | None = None,
        attachment_name: str | None = None,
        attachment_bytes: bytes | None = None,
    ) -> Task:
        """Update an existing task verifying state rules and attachments."""
        task = await self.get_task_by_id(task_id, user_id)
        old_status = task.status
        now = datetime.datetime.now(datetime.UTC)

        # 1. State machine validation
        if status:
            self._verify_state_transition(task.status, status)
            task.status = status

            # Transition actions
            if status == TaskStatus.DONE:
                task.actual_end_time = now
                duration = (now - task.start_time).total_seconds()
                task.total_time_taken_seconds = int(duration)

        # 2. Field updates
        if task_name is not None:
            task.task_name = task_name
        if description is not None:
            task.description = description

        # 3. Expected time updates
        if expected_end_time is not None:
            if expected_end_time.tzinfo is None:
                expected_end_time = expected_end_time.replace(tzinfo=datetime.UTC)

            task_start_time = task.start_time
            if task_start_time.tzinfo is None:
                task_start_time = task_start_time.replace(tzinfo=datetime.UTC)

            if expected_end_time < task_start_time:
                raise BadRequestException(
                    "Expected end time cannot be earlier than start time."
                )
            task.expected_end_time = expected_end_time

        # 4. Attachment updates
        if attachment_name and attachment_bytes:
            self._validate_attachment(attachment_name, attachment_bytes)

            # Clean up old file
            if task.attachment_path:
                with contextlib.suppress(Exception):
                    await self.storage_provider.delete_file(task.attachment_path)

            task.attachment_path = await self.storage_provider.save_file(
                attachment_name, attachment_bytes
            )

        # Log Audit
        metadata = {}
        if old_status != task.status:
            metadata.update(
                {"old_status": old_status.value, "new_status": task.status.value}
            )
        else:
            metadata.update({"task_name": task.task_name})

        await self.audit_service.log_action(
            user_id=user_id,
            action="task_update",
            entity_type="task",
            entity_id=str(task.id),
            metadata=metadata,
        )

        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def soft_delete_task(self, task_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Soft-delete a task by setting its deleted_at field."""
        task = await self.get_task_by_id(task_id, user_id)
        task.deleted_at = datetime.datetime.now(datetime.UTC)

        # Log Audit
        await self.audit_service.log_action(
            user_id=user_id,
            action="task_delete",
            entity_type="task",
            entity_id=str(task.id),
        )

        await self.session.commit()

    async def get_status_counts(self, user_id: uuid.UUID) -> dict[str, int]:
        """Fetch dashboard count stats."""
        raw_counts = await self.repository.get_status_counts(user_id)
        return {status.value: count for status, count in raw_counts.items()}
