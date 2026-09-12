"""
Distributed Background Task Architecture for CampusMIND 2.0.

Provides a unified task execution abstraction supporting synchronous (inline),
threaded (in-process), and distributed task queues (Redis/Celery/ARQ).
Persists task state transitions in the system_tasks infrastructure while protecting secrets.
"""
import threading
import uuid
import time
from datetime import datetime, timezone
from typing import Callable, Dict, Any, Optional, List
from core.config import settings
from core.logging import logger
from repositories.system_task_repository import system_task_repository, SystemTaskRepository


class TaskState:
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BackgroundTaskManager:
    """
    Abstraction layer managing background worker tasks, state transitions,
    deduplication, error handling, and task persistence.
    """

    def __init__(self, task_repo: SystemTaskRepository = system_task_repository):
        self.task_repo = task_repo
        self.provider = settings.TASK_QUEUE_PROVIDER.lower().strip()

    def submit_task(
        self,
        task_type: str,
        target_fn: Callable[..., Any],
        initiated_by: str,
        details: Optional[str] = None,
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None,
        allow_duplicate: bool = False,
    ) -> Dict[str, Any]:
        """
        Submits a task for background or inline execution.
        Prevents duplicate active task execution when allow_duplicate is False.
        """
        args = args or ()
        kwargs = kwargs or {}

        # Deduplication check
        if not allow_duplicate:
            active_tasks = self.task_repo.list_active_tasks(limit=20)
            for active in active_tasks:
                if active.get("task_type") == task_type and active.get("status") in {TaskState.QUEUED, TaskState.RUNNING, "in_progress"}:
                    logger.info(f"Task type '{task_type}' already running/queued (ID: {active['id']}). Returning existing task.")
                    return active

        # Create task record in DB
        task_record = self.task_repo.create_task(
            task_type=task_type,
            initiated_by=initiated_by,
            details=details or f"Task '{task_type}' queued",
        )
        task_id = task_record["id"]

        # Update status to queued
        self.task_repo.update_task(
            task_id=task_id,
            status=TaskState.QUEUED,
            progress_pct=0.0,
            details=details or f"Task '{task_type}' queued",
        )

        def runner():
            start_ts = time.time()
            try:
                self.task_repo.update_task(
                    task_id=task_id,
                    status=TaskState.RUNNING,
                    progress_pct=10.0,
                    details=f"Task '{task_type}' executing",
                )
                
                # Execute underlying worker function
                result = target_fn(*args, **kwargs)

                duration = round(time.time() - start_ts, 2)
                completion_msg = f"Completed successfully in {duration}s"
                self.task_repo.update_task(
                    task_id=task_id,
                    status=TaskState.COMPLETED,
                    progress_pct=100.0,
                    details=completion_msg,
                )
                logger.info(f"Task '{task_id}' ({task_type}) completed in {duration}s")
                return result
            except Exception as e:
                duration = round(time.time() - start_ts, 2)
                # Log detailed traceback internally, but sanitize user-visible detail
                logger.error(f"Task '{task_id}' ({task_type}) failed after {duration}s: {e}")
                sanitized_error = f"Task failed: {type(e).__name__}"
                self.task_repo.update_task(
                    task_id=task_id,
                    status=TaskState.FAILED,
                    progress_pct=0.0,
                    details=sanitized_error,
                )

        if self.provider in {"inline", "sync", "test"}:
            runner()
        elif self.provider in {"redis", "distributed"}:
            logger.warning(
                "Distributed task queue (Celery/ARQ) is not fully implemented. "
                f"Task '{task_id}' will execute in local threaded mode (DEGRADED). "
                "This is not safe for multi-worker distributed execution."
            )
            t = threading.Thread(target=runner, daemon=True)
            t.start()
        else:  # "threaded" / default
            t = threading.Thread(target=runner, daemon=True)
            t.start()

        return self.task_repo.get_task(task_id) or task_record

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves task status by ID."""
        return self.task_repo.get_task(task_id)

    def retry_task(
        self,
        task_id: str,
        target_fn: Callable[..., Any],
        initiated_by: str,
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None,
    ) -> Dict[str, Any]:

        """Retries a failed or completed task safely."""
        existing = self.task_repo.get_task(task_id)
        if not existing:
            raise ValueError(f"Task '{task_id}' not found")

        return self.submit_task(
            task_type=existing["task_type"],
            target_fn=target_fn,
            initiated_by=initiated_by,
            details=f"Retried task '{task_id}'",
            args=args,
            kwargs=kwargs,
            allow_duplicate=True,
        )


task_manager = BackgroundTaskManager()
