import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.task import Task, TaskStatus
from src.services.scheduler import run_scheduler


@pytest.mark.asyncio
async def test_scheduler_run_success():
    """Test standard execution of scheduler loop finding and marking expired tasks."""
    mock_task = MagicMock(spec=Task)
    mock_task.id = "test-task-id"
    mock_task.user_id = "test-user-id"
    mock_task.status = TaskStatus.PENDING

    mock_session = AsyncMock()
    mock_task_repo = AsyncMock()
    mock_task_repo.get_expired_active_tasks.return_value = [mock_task]

    mock_session_local = MagicMock()
    mock_session_local.return_value.__aenter__.return_value = mock_session

    sleep_count = 0

    async def mock_sleep(_seconds: float) -> None:
        nonlocal sleep_count
        sleep_count += 1
        if sleep_count > 1:
            raise asyncio.CancelledError()

    with (
        patch("src.services.scheduler.SessionLocal", mock_session_local),
        patch("src.services.scheduler.TaskRepository", return_value=mock_task_repo),
        patch("src.services.scheduler.asyncio.sleep", side_effect=mock_sleep),
        patch("src.services.scheduler.AuditService") as mock_audit_service_class,
    ):
        mock_audit = AsyncMock()
        mock_audit_service_class.return_value = mock_audit

        await run_scheduler(interval_seconds=1)

        mock_session_local.assert_called_once()
        mock_task_repo.get_expired_active_tasks.assert_called_once()
        assert mock_task.status == TaskStatus.MISSED
        mock_audit.log_action.assert_called_once()
        mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_scheduler_run_exception():
    """Test scheduler loop exception handling does not crash the loop."""
    mock_session_local = MagicMock()
    mock_session_local.return_value.__aenter__.side_effect = Exception(
        "DB Connection Error"
    )

    sleep_count = 0

    async def mock_sleep(_seconds: float) -> None:
        nonlocal sleep_count
        sleep_count += 1
        if sleep_count > 1:
            raise asyncio.CancelledError()

    with (
        patch("src.services.scheduler.SessionLocal", mock_session_local),
        patch("src.services.scheduler.asyncio.sleep", side_effect=mock_sleep),
    ):
        await run_scheduler(interval_seconds=1)
        mock_session_local.assert_called_once()
