from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository providing generic CRUD database access. Does not commit transactions."""

    def __init__(self, model: type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: Any) -> T | None:
        """Fetch a single record by its primary key ID."""
        return await self.session.get(self.model, id)

    async def get_all(self, offset: int = 0, limit: int = 100) -> list[T]:
        """Fetch all records with basic pagination."""
        query = select(self.model).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, entity: T) -> T:
        """Add a new record to the session state."""
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def delete(self, entity: T) -> None:
        """Remove a record from the database."""
        await self.session.delete(entity)
        await self.session.flush()
