"""Announcement Service for CampusMIND 2.0.

Implements RBAC-restricted business logic for institutional announcements and targeting.
"""
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from db.session import get_db_session
from db.models import User, Announcement
from models.schemas import UserSchema
from repositories.announcement_repository import announcement_repository
from repositories.audit_repository import audit_repository


class AnnouncementService:
    def create_announcement(self, user: UserSchema, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a new institutional announcement.
        Strictly forbidden for students.
        """
        if user.role == "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students are not authorized to create announcements."
            )

        with get_db_session() as session:
            actor = session.query(User).filter(User.username == user.username).first()
            ann_data = {
                "title": data["title"],
                "content": data["content"],
                "author_id": actor.id if actor else "usr_admin1",
                "audience": data.get("audience", "all"),
                "department_id": data.get("department_id"),
                "program_id": data.get("program_id"),
                "course_id": data.get("course_id"),
                "status": data.get("status", "published"),
                "priority": data.get("priority", "normal"),
                "publish_at": data.get("publish_at"),
                "expires_at": data.get("expires_at"),
            }
            ann = announcement_repository.create_announcement(session, ann_data)
            
            audit_repository.log_audit_event(
                event_type="ANNOUNCEMENT_CREATED",
                actor_username=user.username,
                user_id=actor.id if actor else None,
                details=f"Created announcement '{ann.title}' for audience '{ann.audience}'"
            )

            return {
                "id": ann.id,
                "title": ann.title,
                "content": ann.content,
                "audience": ann.audience,
                "priority": ann.priority,
                "status": ann.status,
                "created_at": ann.created_at.isoformat() if hasattr(ann.created_at, "isoformat") else str(ann.created_at),
            }

    def list_announcements(
        self,
        user: UserSchema,
        department_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Lists announcements targeted for the user's role and department."""
        audience_filter = ["all"]
        if user.role == "student":
            audience_filter.append("students")
        elif user.role == "faculty":
            audience_filter.extend(["faculty", "students"])
        elif user.role == "admin":
            audience_filter.extend(["admin", "faculty", "students"])

        with get_db_session() as session:
            announcements = announcement_repository.list_announcements(
                session,
                audience_filter=audience_filter,
                department_id=department_id,
                status="published",
                limit=limit,
                offset=offset,
            )
            total = announcement_repository.count_announcements(
                session,
                audience_filter=audience_filter,
                department_id=department_id,
                status="published",
            )

            results = [
                {
                    "id": a.id,
                    "title": a.title,
                    "content": a.content,
                    "author_name": a.author.display_name if a.author else None,
                    "audience": a.audience,
                    "priority": a.priority,
                    "created_at": a.created_at.isoformat() if hasattr(a.created_at, "isoformat") else str(a.created_at),
                }
                for a in announcements
            ]

            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "announcements": results,
            }


announcement_service = AnnouncementService()
