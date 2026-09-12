"""
System Task Data Repository for CampusMIND 2.0.
Encapsulates operations for background worker tasks, RAG evaluations, and ingestion job tracking.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import select, desc
from db.session import get_db_session
from db.models import SystemTask, utc_now
from core.logging import logger


class SystemTaskRepository:
    """Repository managing background system task execution status."""

    def create_task(
        self,
        task_type: str,
        initiated_by: str,
        details: Optional[str] = None
    ) -> Dict[str, Any]:
        """Creates and tracks a new background task."""
        task_id = f"task_{uuid.uuid4().hex[:10]}"
        now = utc_now()
        task_data = {
            "id": task_id,
            "task_type": task_type,
            "status": "in_progress",
            "progress_pct": 0.0,
            "details": details or f"Task {task_type} initiated",
            "initiated_by": initiated_by,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        try:
            with get_db_session() as session:
                task = SystemTask(
                    id=task_id,
                    task_type=task_type,
                    status="in_progress",
                    progress_pct=0.0,
                    details=details,
                    initiated_by=initiated_by,
                    created_at=now,
                    updated_at=now,
                )
                session.add(task)
        except Exception as e:
            logger.debug(f"Failed to persist SystemTask in DB: {e}")

        return task_data

    def update_task(
        self,
        task_id: str,
        status: str,
        progress_pct: float,
        details: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Updates status, progress, and details of a system task."""
        now = utc_now()
        try:
            with get_db_session() as session:
                task = session.get(SystemTask, task_id)
                if task:
                    task.status = status
                    task.progress_pct = progress_pct
                    if details:
                        task.details = details
                    task.updated_at = now
                    return {
                        "id": task.id,
                        "task_type": task.task_type,
                        "status": task.status,
                        "progress_pct": task.progress_pct,
                        "details": task.details,
                        "initiated_by": task.initiated_by,
                        "created_at": task.created_at.isoformat() if hasattr(task.created_at, "isoformat") else str(task.created_at),
                        "updated_at": task.updated_at.isoformat() if hasattr(task.updated_at, "isoformat") else str(task.updated_at),
                    }
        except Exception as e:
            logger.debug(f"Failed to update SystemTask in DB: {e}")

        return None

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves system task by ID."""
        try:
            with get_db_session() as session:
                task = session.get(SystemTask, task_id)
                if task:
                    return {
                        "id": task.id,
                        "task_type": task.task_type,
                        "status": task.status,
                        "progress_pct": task.progress_pct,
                        "details": task.details,
                        "initiated_by": task.initiated_by,
                        "created_at": task.created_at.isoformat() if hasattr(task.created_at, "isoformat") else str(task.created_at),
                        "updated_at": task.updated_at.isoformat() if hasattr(task.updated_at, "isoformat") else str(task.updated_at),
                    }
        except Exception as e:
            logger.debug(f"Failed to fetch SystemTask from DB: {e}")

        return None

    def list_active_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Lists recent system tasks."""
        try:
            with get_db_session() as session:
                tasks = session.scalars(
                    select(SystemTask).order_by(desc(SystemTask.created_at)).limit(limit)
                ).all()
                return [
                    {
                        "id": t.id,
                        "task_type": t.task_type,
                        "status": t.status,
                        "progress_pct": t.progress_pct,
                        "details": t.details,
                        "initiated_by": t.initiated_by,
                        "created_at": t.created_at.isoformat() if hasattr(t.created_at, "isoformat") else str(t.created_at),
                        "updated_at": t.updated_at.isoformat() if hasattr(t.updated_at, "isoformat") else str(t.updated_at),
                    }
                    for t in tasks
                ]
        except Exception as e:
            logger.debug(f"Failed to list system tasks from DB: {e}")

        return []


system_task_repository = SystemTaskRepository()
