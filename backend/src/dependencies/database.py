from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Expose database session generator as a dependency."""
    async for session in get_db():
        yield session
