import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.audit import AuditLog
from src.repositories.audit import AuditRepository


@pytest.mark.asyncio
async def test_audit_repository_get_audits(db_session: AsyncSession):
    """Test AuditRepository get_audits sorting, filtering, and fallback behavior."""
    repo = AuditRepository(db_session)

    # Create dummy audit log
    log = AuditLog(
        user_id=None,
        action="test_action",
        entity_type="test_entity",
        entity_id="123",
        action_metadata={"foo": "bar"},
    )
    await repo.create(log)
    await db_session.commit()

    # Retrieve audits
    logs, total = await repo.get_audits(
        user_id=None,
        offset=0,
        limit=10,
        sort_by="created_at",
        sort_order="desc",
    )
    assert total >= 1
    assert len(logs) >= 1

    # Retrieve audits with invalid sort column (should fallback to created_at)
    _, total_invalid = await repo.get_audits(
        user_id=None,
        offset=0,
        limit=10,
        sort_by="invalid_col",
        sort_order="asc",
    )
    assert total_invalid >= 1

    # Retrieve audits with user_id filter
    _, total_user = await repo.get_audits(
        user_id=uuid.uuid4(),
        offset=0,
        limit=10,
    )
    assert total_user == 0

    # Retrieve all logs (base repository get_all)
    all_logs = await repo.get_all(offset=0, limit=10)
    assert len(all_logs) >= 1

    # Delete log (base repository delete)
    await repo.delete(log)
    await db_session.commit()
