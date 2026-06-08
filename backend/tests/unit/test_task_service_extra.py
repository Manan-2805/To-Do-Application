import datetime
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import BadRequestException, EntityNotFoundException
from src.models.task import TaskStatus
from src.services.auth import AuthService
from src.services.task import TaskService


@pytest.mark.asyncio
async def test_task_service_invalid_transitions(db_session: AsyncSession):
    auth_service = AuthService(db_session)
    user = await auth_service.register_user(
        username="transition_u", password="Password123!"
    )

    task_service = TaskService(db_session)
    tomorrow = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)

    task = await task_service.create_task(
        user_id=user.id,
        task_name="Transition Task",
        description="Check invalid transitions",
        expected_end_time=tomorrow,
    )

    # Attempt invalid Pending -> Done transition directly (should raise BadRequestException)
    with pytest.raises(BadRequestException):
        await task_service.update_task(
            task_id=task.id, user_id=user.id, status=TaskStatus.DONE
        )

    # Transition Pending -> In Progress (valid)
    task = await task_service.update_task(
        task_id=task.id, user_id=user.id, status=TaskStatus.IN_PROGRESS
    )
    assert task.status == TaskStatus.IN_PROGRESS

    # Transition In Progress -> Done (valid)
    task = await task_service.update_task(
        task_id=task.id, user_id=user.id, status=TaskStatus.DONE
    )
    assert task.status == TaskStatus.DONE

    # Attempt Done -> In Progress (invalid)
    with pytest.raises(BadRequestException):
        await task_service.update_task(
            task_id=task.id, user_id=user.id, status=TaskStatus.IN_PROGRESS
        )


@pytest.mark.asyncio
async def test_task_service_soft_delete_non_existent(db_session: AsyncSession):
    task_service = TaskService(db_session)
    random_id = uuid.uuid4()
    with pytest.raises(EntityNotFoundException):
        await task_service.soft_delete_task(random_id, uuid.uuid4())


@pytest.mark.asyncio
async def test_task_service_attachment_validation(db_session: AsyncSession):
    auth_service = AuthService(db_session)
    user = await auth_service.register_user(
        username="attachment_u", password="Password123!"
    )

    task_service = TaskService(db_session)
    tomorrow = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)

    # 1. Invalid Extension
    with pytest.raises(BadRequestException):
        await task_service.create_task(
            user_id=user.id,
            task_name="Task with invalid attachment",
            description="Txt file",
            expected_end_time=tomorrow,
            attachment_name="document.txt",
            attachment_bytes=b"some text content",
        )

    # 2. File size limit exceeded (>5 MB)
    large_bytes = b"0" * (5 * 1024 * 1024 + 1)
    with pytest.raises(BadRequestException):
        await task_service.create_task(
            user_id=user.id,
            task_name="Task with large attachment",
            description="Large file",
            expected_end_time=tomorrow,
            attachment_name="image.png",
            attachment_bytes=large_bytes,
        )


@pytest.mark.asyncio
async def test_task_service_attachment_replacement(db_session: AsyncSession):
    auth_service = AuthService(db_session)
    user = await auth_service.register_user(
        username="replacement_u", password="Password123!"
    )

    task_service = TaskService(db_session)
    tomorrow = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=1)

    # Create task with first attachment
    task = await task_service.create_task(
        user_id=user.id,
        task_name="Task with attachment",
        description="First attachment",
        expected_end_time=tomorrow,
        attachment_name="first.png",
        attachment_bytes=b"first_content",
    )
    first_path = task.attachment_path
    assert first_path is not None

    # Update task with second attachment (should replace first attachment)
    updated_task = await task_service.update_task(
        task_id=task.id,
        user_id=user.id,
        attachment_name="second.png",
        attachment_bytes=b"second_content",
    )
    assert updated_task.attachment_path is not None
    assert updated_task.attachment_path != first_path
