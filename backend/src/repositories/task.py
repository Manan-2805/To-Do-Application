import datetime
import uuid

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.task import Task, TaskStatus
from src.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """Repository managing Task db access with soft-delete filtering."""

    def __init__(self, session: AsyncSession):
        super().__init__(Task, session)

    async def get_by_id_for_user(
        self, task_id: uuid.UUID, user_id: uuid.UUID
    ) -> Task | None:
        """Fetch active task for user, filtering out soft-deleted."""
        query = select(Task).where(
            and_(Task.id == task_id, Task.user_id == user_id, Task.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_tasks_for_user(
        self,
        user_id: uuid.UUID,
        status: TaskStatus | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 10,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Task], int]:
        """Query tasks for a user applying search, status filter, and custom sorting/pagination."""
        # Base filter: belonging to user & not soft-deleted
        filters = [Task.user_id == user_id, Task.deleted_at.is_(None)]

        if status:
            filters.append(Task.status == status)
        if search:
            filters.append(Task.task_name.ilike(f"%{search}%"))

        # Count total matches
        count_query = select(func.count()).select_from(Task).where(and_(*filters))
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar_one_or_none() or 0

        # Sort and Page
        query = select(Task).where(and_(*filters))
        sort_attr = getattr(Task, sort_by, None)
        if sort_attr is None:
            sort_attr = Task.created_at

        if sort_order == "desc":
            query = query.order_by(sort_attr.desc())
        else:
            query = query.order_by(sort_attr.asc())

        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all()), total_count

    async def get_status_counts(self, user_id: uuid.UUID) -> dict[TaskStatus, int]:
        """Calculate counts grouped by status for dashboard statistics."""
        query = (
            select(Task.status, func.count(Task.id))
            .where(and_(Task.user_id == user_id, Task.deleted_at.is_(None)))
            .group_by(Task.status)
        )
        result = await self.session.execute(query)

        counts = dict.fromkeys(TaskStatus, 0)
        for status, count in result.all():
            counts[status] = count
        return counts

    async def get_expired_active_tasks(self) -> list[Task]:
        """Retrieve active tasks (Pending or In Progress) past expected_end_time."""
        now = datetime.datetime.now(datetime.UTC)
        query = select(Task).where(
            and_(
                Task.deleted_at.is_(None),
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                Task.expected_end_time < now,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
