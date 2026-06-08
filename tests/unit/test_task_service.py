import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import BadRequestException, EntityNotFoundException
from src.models.task import TaskStatus
from src.services.auth import AuthService
from src.services.task import TaskService


@pytest.mark.asyncio
async def test_task_service_create_success(db_session: AsyncSession):
    """Test successful task creation and initial field defaults."""
    auth_service = AuthService(db_session)
    user = await auth_service.register_user(username="task_u1", password="Password123!")

    task_service = TaskService(db_session)
    tomorrow = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)

    task = await task_service.create_task(
        user_id=user.id,
        task_name="Write Unit Test",
        description="Verify task service logic.",
        expected_end_time=tomorrow,
    )

    assert task.id is not None
    assert task.status == TaskStatus.PENDING
    assert task.task_name == "Write Unit Test"
    assert task.deleted_at is None


@pytest.mark.asyncio
async def test_task_service_create_invalid_time(db_session: AsyncSession):
    """Test task creation failure when deadline is in the past."""
    auth_service = AuthService(db_session)
    user = await auth_service.register_user(username="task_u2", password="Password123!")

    task_service = TaskService(db_session)
    yesterday = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=1)

    with pytest.raises(BadRequestException):
        await task_service.create_task(
            user_id=user.id,
            task_name="Fail Task",
            description="Should not succeed",
            expected_end_time=yesterday,
        )


@pytest.mark.asyncio
async def test_task_service_transitions(db_session: AsyncSession):
    """Test transitions conform to state machine constraints."""
    auth_service = AuthService(db_session)
    user = await auth_service.register_user(username="task_u3", password="Password123!")

    task_service = TaskService(db_session)
    tomorrow = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)

    task = await task_service.create_task(
        user_id=user.id,
        task_name="Transition Task",
        description="Check status rules.",
        expected_end_time=tomorrow,
    )

    # 1. Pending -> In Progress
    task = await task_service.update_task(
        task_id=task.id, user_id=user.id, status=TaskStatus.IN_PROGRESS
    )
    assert task.status == TaskStatus.IN_PROGRESS

    # 2. In Progress -> Done
    task = await task_service.update_task(
        task_id=task.id, user_id=user.id, status=TaskStatus.DONE
    )
    assert task.status == TaskStatus.DONE
    assert task.actual_end_time is not None
    assert task.total_time_taken_seconds is not None

    # 3. Done -> Pending should fail
    with pytest.raises(BadRequestException):
        await task_service.update_task(
            task_id=task.id, user_id=user.id, status=TaskStatus.PENDING
        )


@pytest.mark.asyncio
async def test_task_service_soft_delete(db_session: AsyncSession):
    """Test task deletion sets deleted_at and hides record from lists."""
    auth_service = AuthService(db_session)
    user = await auth_service.register_user(username="task_u4", password="Password123!")

    task_service = TaskService(db_session)
    tomorrow = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)

    task = await task_service.create_task(
        user_id=user.id,
        task_name="Delete Task",
        description="Soft delete task.",
        expected_end_time=tomorrow,
    )

    await task_service.soft_delete_task(task.id, user.id)

    # Check that query raises EntityNotFoundException
    with pytest.raises(EntityNotFoundException):
        await task_service.get_task_by_id(task.id, user.id)

    # Check that task list is empty
    tasks, count = await task_service.get_tasks(user_id=user.id)
    assert count == 0
    assert len(tasks) == 0
