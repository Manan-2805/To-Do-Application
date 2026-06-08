import asyncio
import datetime
import logging
import os
import random

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.core.security import hash_password
from src.models.audit import AuditLog
from src.models.base import Base
from src.models.task import Task, TaskStatus
from src.models.user import User


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("todosphere.ci_seed")

fake = Faker()

NUM_USERS = 10
TASKS_PER_USER_MIN = 20
TASKS_PER_USER_MAX = 30

ALL_STATUSES = [
    TaskStatus.PENDING,
    TaskStatus.IN_PROGRESS,
    TaskStatus.DONE,
    TaskStatus.MISSED,
]


async def seed(database_url: str) -> None:
    """Seed the CI database with faker-generated users, tasks, and audit logs."""
    engine = create_async_engine(database_url, echo=False, poolclass=NullPool)
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    logger.info("Creating all tables in CI database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        now = datetime.datetime.now(datetime.UTC)

        for i in range(NUM_USERS):
            username = f"ci_user_{i}_{fake.user_name()[:12]}"
            hashed_pw = hash_password("CiPassword123!")
            user = User(username=username, hashed_password=hashed_pw)
            session.add(user)
            await session.flush()

            session.add(
                AuditLog(
                    user_id=user.id,
                    action="signup",
                    entity_type="user",
                    entity_id=str(user.id),
                    metadata={"username": username},
                    ip_address=fake.ipv4(),
                    user_agent=fake.user_agent(),
                )
            )
            session.add(
                AuditLog(
                    user_id=user.id,
                    action="login",
                    entity_type="user",
                    entity_id=str(user.id),
                    ip_address=fake.ipv4(),
                    user_agent=fake.user_agent(),
                )
            )

            task_count = random.randint(TASKS_PER_USER_MIN, TASKS_PER_USER_MAX)
            for _ in range(task_count):
                status = random.choice(ALL_STATUSES)
                start_offset = random.randint(-14, -1)
                start_time = now + datetime.timedelta(days=start_offset)

                if status in (TaskStatus.DONE, TaskStatus.MISSED):
                    expected_end_time = start_time + datetime.timedelta(
                        hours=random.randint(1, 48)
                    )
                else:
                    expected_end_time = now + datetime.timedelta(
                        days=random.randint(1, 14)
                    )

                actual_end_time = None
                total_time_taken_seconds = None
                if status == TaskStatus.DONE:
                    delta_seconds = int(
                        (expected_end_time - start_time).total_seconds()
                    )
                    actual_seconds = random.randint(60, max(60, delta_seconds))
                    actual_end_time = start_time + datetime.timedelta(
                        seconds=actual_seconds
                    )
                    total_time_taken_seconds = actual_seconds

                task = Task(
                    user_id=user.id,
                    task_name=fake.bs().capitalize()[:120],
                    description=fake.paragraph(nb_sentences=2),
                    status=status,
                    start_time=start_time,
                    expected_end_time=expected_end_time,
                    actual_end_time=actual_end_time,
                    total_time_taken_seconds=total_time_taken_seconds,
                )
                session.add(task)
                await session.flush()

                session.add(
                    AuditLog(
                        user_id=user.id,
                        action="task_create",
                        entity_type="task",
                        entity_id=str(task.id),
                        metadata={"task_name": task.task_name},
                        ip_address=fake.ipv4(),
                        user_agent=fake.user_agent(),
                        created_at=start_time,
                    )
                )

                if status == TaskStatus.DONE:
                    session.add(
                        AuditLog(
                            user_id=user.id,
                            action="task_update",
                            entity_type="task",
                            entity_id=str(task.id),
                            metadata={"old_status": "Pending", "new_status": "Done"},
                            ip_address=fake.ipv4(),
                            user_agent=fake.user_agent(),
                            created_at=actual_end_time,
                        )
                    )

            logger.info(
                "Seeded user %d/%d: %s with %d tasks",
                i + 1,
                NUM_USERS,
                username,
                task_count,
            )

        await session.commit()

    await engine.dispose()
    logger.info("CI database seeding completed.")


if __name__ == "__main__":
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is required")
    asyncio.run(seed(db_url))
