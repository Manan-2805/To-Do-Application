import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.audit import AuditLog
from src.repositories.audit import AuditRepository


class AuditService:
    """Service layer coordinating audit logging and query retrieval."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = AuditRepository(session)

    async def log_action(
        self,
        user_id: uuid.UUID | None,
        action: str,
        entity_type: str,
        entity_id: str | None = None,
        metadata: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Create and write an audit record to DB state (does not commit)."""
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            action_metadata=metadata,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return await self.repository.create(log_entry)

    async def get_audits(
        self,
        user_id: uuid.UUID | None = None,
        offset: int = 0,
        limit: int = 10,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[AuditLog], int]:
        """Fetch audit records for user (or all if user_id is None)."""
        return await self.repository.get_audits(
            user_id=user_id,
            offset=offset,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )
