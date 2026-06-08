import asyncio
import contextlib
import os
import urllib.parse
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


# Set TESTING env var before importing src models/main
os.environ["TESTING"] = "True"

from src.core.config import settings
from src.database import get_db
from src.dependencies.database import get_db_session
from src.main import app
from src.models.base import Base


parsed_url = urllib.parse.urlparse(settings.DATABASE_URL)
TEST_DATABASE_URL = parsed_url._replace(path=parsed_url.path + "_test").geturl()

test_engine = create_async_engine(
    TEST_DATABASE_URL, echo=False, future=True, poolclass=NullPool
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    """Build test tables and clean up on test completion."""
    # Ensure test database exists
    base_db_url, _ = settings.DATABASE_URL.rsplit("/", 1)
    postgres_url = f"{base_db_url}/postgres"

    parsed_test_url = urllib.parse.urlparse(TEST_DATABASE_URL)
    test_db_name = parsed_test_url.path.lstrip("/")

    temp_engine = create_async_engine(postgres_url, isolation_level="AUTOCOMMIT")
    async with temp_engine.connect() as conn:
        with contextlib.suppress(Exception):
            await conn.execute(text(f'CREATE DATABASE "{test_db_name}"'))
    await temp_engine.dispose()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated database transaction per test run."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture(autouse=True)
def override_db_dependency(db_session: AsyncSession):
    """Register FastAPI overrides for dependencies."""

    async def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db_session] = _get_test_db
    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Supply async HTTPX client for testing FastAPI routers."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
