import uuid

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.audit import AuditLog
from src.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    """Repository managing AuditLog db access with sorting and pagination."""

    def __init__(self, session: AsyncSession):
        super().__init__(AuditLog, session)

    async def get_audits(
        self,
        user_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 10,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[AuditLog], int]:
        """Fetch audit logs, optionally filtered by user_id, with sorting/pagination."""
        filters = []
        if user_id:
            filters.append(AuditLog.user_id == user_id)

        # Count total matches
        count_query = select(func.count()).select_from(AuditLog)
        if filters:
            count_query = count_query.where(and_(*filters))
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar_one_or_none() or 0

        # Sort and Page
        query = select(AuditLog)
        if filters:
            query = query.where(and_(*filters))

        sort_attr = getattr(AuditLog, sort_by, None)
        if sort_attr is None:
            sort_attr = AuditLog.created_at

        if sort_order == "desc":
            query = query.order_by(sort_attr.desc())
        else:
            query = query.order_by(sort_attr.asc())

        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all()), total_count
