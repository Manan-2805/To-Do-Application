import asyncio
import logging

from src.database import SessionLocal
from src.models.task import TaskStatus
from src.repositories.task import TaskRepository
from src.services.audit import AuditService


logger = logging.getLogger("todosphere.scheduler")


async def run_scheduler(interval_seconds: int = 60) -> None:
    """Asynchronous background loop looking for tasks past their expected deadline and marking them Missed."""
    logger.info("Starting background Task Status Scheduler...")

    while True:
        try:
            await asyncio.sleep(interval_seconds)

            # Start fresh session for check
            async with SessionLocal() as session:
                task_repo = TaskRepository(session)
                expired_tasks = await task_repo.get_expired_active_tasks()

                if expired_tasks:
                    logger.info(
                        f"Scheduler found {len(expired_tasks)} expired tasks. Updating to Missed..."
                    )
                    audit_service = AuditService(session)

                    for task in expired_tasks:
                        old_status = task.status
                        task.status = TaskStatus.MISSED

                        await audit_service.log_action(
                            user_id=task.user_id,
                            action="task_scheduler_update",
                            entity_type="task",
                            entity_id=str(task.id),
                            metadata={
                                "old_status": old_status.value,
                                "new_status": TaskStatus.MISSED.value,
                            },
                        )

                    await session.commit()
                    logger.info("Successfully updated expired tasks.")

        except asyncio.CancelledError:
            logger.info("Scheduler task was cancelled. Shutting down scheduler.")
            break
        except Exception as e:
            logger.error(
                f"Error occurred in background status scheduler: {e!s}",
                exc_info=True,
            )
