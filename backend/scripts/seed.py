import asyncio
import datetime
import logging

from src.core.security import hash_password
from src.database import SessionLocal, engine
from src.models import Base
from src.models.audit import AuditLog
from src.models.task import Task, TaskStatus
from src.models.user import User


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("todosphere.seed")


async def seed_data():
    """Seed the database with a test user and various tasks across status configurations."""
    logger.info("Initializing database schema for seeding...")

    # Ensure tables are created directly for dev/test convenience
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        # Check if user already exists
        user_username = "demo_user"
        existing_user = await session.run_sync(
            lambda s: s.query(User).filter_by(username=user_username).first()
        )

        if existing_user:
            logger.info("Demo user already exists. Seeding aborted.")
            return

        logger.info("Creating demo user profile...")
        hashed_pw = hash_password("Password123!")
        user = User(username=user_username, hashed_password=hashed_pw)
        session.add(user)
        await session.flush()  # Populate user.id

        # Log signup audit
        signup_audit = AuditLog(
            user_id=user.id,
            action="signup",
            entity_type="user",
            entity_id=str(user.id),
            metadata={"username": user_username},
            ip_address="127.0.0.1",
            user_agent="Seed Script",
        )
        session.add(signup_audit)

        # Log login audit
        login_audit = AuditLog(
            user_id=user.id,
            action="login",
            entity_type="user",
            entity_id=str(user.id),
            ip_address="127.0.0.1",
            user_agent="Seed Script",
        )
        session.add(login_audit)

        logger.info("Seeding sample tasks...")
        now = datetime.datetime.now(datetime.UTC)

        tasks_data = [
            # Pending Tasks
            {
                "task_name": "Review Project Proposal",
                "description": "Read through the new TodoSphere requirements doc.",
                "status": TaskStatus.PENDING,
                "start_time": now - datetime.timedelta(hours=2),
                "expected_end_time": now + datetime.timedelta(days=2),
            },
            {
                "task_name": "Buy Groceries",
                "description": "Milk, eggs, spinach, coffee beans.",
                "status": TaskStatus.PENDING,
                "start_time": now,
                "expected_end_time": now + datetime.timedelta(hours=5),
            },
            {
                "task_name": "Plan Summer Vacation",
                "description": "Look up flight deals and hotel reviews.",
                "status": TaskStatus.PENDING,
                "start_time": now,
                "expected_end_time": now + datetime.timedelta(days=10),
            },
            # In Progress Tasks
            {
                "task_name": "Implement API Routers",
                "description": "Write FastAPI routers for auth, tasks and audits.",
                "status": TaskStatus.IN_PROGRESS,
                "start_time": now - datetime.timedelta(hours=4),
                "expected_end_time": now + datetime.timedelta(hours=8),
            },
            {
                "task_name": "Design Custom Chart",
                "description": "Craft responsive SVG-based pie chart component.",
                "status": TaskStatus.IN_PROGRESS,
                "start_time": now - datetime.timedelta(hours=1),
                "expected_end_time": now + datetime.timedelta(hours=4),
            },
            # Done Tasks (Requires total_time_taken_seconds & actual_end_time)
            {
                "task_name": "Configure Database Schema",
                "description": "Set up PostgreSQL models with SQLAlchemy and Alembic.",
                "status": TaskStatus.DONE,
                "start_time": now - datetime.timedelta(days=1),
                "expected_end_time": now - datetime.timedelta(hours=12),
                "actual_end_time": now - datetime.timedelta(hours=18),
                "total_time_taken_seconds": int(
                    datetime.timedelta(hours=6).total_seconds()
                ),
            },
            {
                "task_name": "Setup Repository Structure",
                "description": "Organize folders and create pyproject.toml.",
                "status": TaskStatus.DONE,
                "start_time": now - datetime.timedelta(days=2),
                "expected_end_time": now - datetime.timedelta(days=1),
                "actual_end_time": now - datetime.timedelta(days=1, hours=20),
                "total_time_taken_seconds": int(
                    datetime.timedelta(hours=4).total_seconds()
                ),
            },
            {
                "task_name": "Initialize Git",
                "description": "Create repo, add .gitignore, and commit initial setup.",
                "status": TaskStatus.DONE,
                "start_time": now - datetime.timedelta(days=3),
                "expected_end_time": now - datetime.timedelta(days=2),
                "actual_end_time": now - datetime.timedelta(days=2, hours=23),
                "total_time_taken_seconds": int(
                    datetime.timedelta(minutes=60).total_seconds()
                ),
            },
            # Missed Tasks (expected_end_time is in past, status is Missed)
            {
                "task_name": "Submit Weekly Timesheet",
                "description": "Log hours and submit in corporate portal.",
                "status": TaskStatus.MISSED,
                "start_time": now - datetime.timedelta(days=4),
                "expected_end_time": now - datetime.timedelta(days=3),
            },
            {
                "task_name": "Schedule Dentist Appointment",
                "description": "Routine dental cleaning appointment.",
                "status": TaskStatus.MISSED,
                "start_time": now - datetime.timedelta(days=7),
                "expected_end_time": now - datetime.timedelta(days=6),
            },
            {
                "task_name": "Renew Gym Membership",
                "description": "Annual renewal process.",
                "status": TaskStatus.MISSED,
                "start_time": now - datetime.timedelta(days=12),
                "expected_end_time": now - datetime.timedelta(days=11),
            },
        ]

        for t_dict in tasks_data:
            task = Task(
                user_id=user.id,
                task_name=t_dict["task_name"],
                description=t_dict.get("description"),
                status=t_dict["status"],
                start_time=t_dict["start_time"],
                expected_end_time=t_dict["expected_end_time"],
                actual_end_time=t_dict.get("actual_end_time"),
                total_time_taken_seconds=t_dict.get("total_time_taken_seconds"),
            )
            session.add(task)
            await session.flush()  # Populate task.id

            # Log task audit
            task_audit = AuditLog(
                user_id=user.id,
                action="task_create",
                entity_type="task",
                entity_id=str(task.id),
                metadata={"task_name": task.task_name},
                ip_address="127.0.0.1",
                user_agent="Seed Script",
                created_at=t_dict["start_time"],
            )
            session.add(task_audit)

            # If done, log task update audit
            if t_dict["status"] == TaskStatus.DONE:
                update_audit = AuditLog(
                    user_id=user.id,
                    action="task_update",
                    entity_type="task",
                    entity_id=str(task.id),
                    metadata={"old_status": "Pending", "new_status": "Done"},
                    ip_address="127.0.0.1",
                    user_agent="Seed Script",
                    created_at=t_dict["actual_end_time"],
                )
                session.add(update_audit)

        await session.commit()
        logger.info("Database seeding successfully completed!")


if __name__ == "__main__":
    asyncio.run(seed_data())
