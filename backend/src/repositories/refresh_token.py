import datetime
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.refresh_token import RefreshToken
from src.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Repository managing RefreshToken db access."""

    def __init__(self, session: AsyncSession):
        super().__init__(RefreshToken, session)

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        """Fetch token metadata using its hash."""
        query = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        """Mark all active refresh tokens for a user as revoked."""
        query = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.datetime.now(datetime.UTC))
        )
        await self.session.execute(query)
        await self.session.flush()
