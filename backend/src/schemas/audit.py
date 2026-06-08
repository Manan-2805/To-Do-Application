import datetime
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    action: str
    entity_type: str
    entity_id: str | None = None
    action_metadata: dict[str, Any] | None = None

    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedAuditResponse(BaseModel):
    audits: list[AuditResponse]
    total_count: int
    page: int
    limit: int
