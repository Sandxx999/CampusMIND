"""Announcement Repository for CampusMIND 2.0.

Provides database access for institutional announcements and targeting.
"""
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from db.models import Announcement, User


class AnnouncementRepository:
    def create_announcement(self, db: Session, data: Dict[str, Any]) -> Announcement:
        """Creates a new institutional announcement."""
        announcement = Announcement(
            id=data.get("id", f"ann_{uuid.uuid4().hex[:12]}"),
            title=data["title"],
            content=data["content"],
            author_id=data["author_id"],
            audience=data.get("audience", "all"),
            department_id=data.get("department_id"),
            program_id=data.get("program_id"),
            course_id=data.get("course_id"),
            status=data.get("status", "published"),
            priority=data.get("priority", "normal"),
            publish_at=data.get("publish_at"),
            expires_at=data.get("expires_at"),
        )
        db.add(announcement)
        db.commit()
        db.refresh(announcement)
        return announcement

    def get_announcement_by_id(self, db: Session, announcement_id: str) -> Optional[Announcement]:
        """Retrieves an announcement by ID."""
        return db.query(Announcement).filter(Announcement.id == announcement_id).first()

    def list_announcements(
        self,
        db: Session,
        audience_filter: Optional[List[str]] = None,
        department_id: Optional[str] = None,
        status: Optional[str] = "published",
        limit: int = 50,
        offset: int = 0,
    ) -> List[Announcement]:
        """Lists announcements matching audience and status filters."""
        query = db.query(Announcement)
        if status:
            query = query.filter(Announcement.status == status)
        if audience_filter:
            query = query.filter(or_(
                Announcement.audience.in_(audience_filter),
                Announcement.audience == "all"
            ))
        if department_id:
            query = query.filter(or_(
                Announcement.department_id == department_id,
                Announcement.department_id.is_(None)
            ))
        return query.order_by(Announcement.created_at.desc()).offset(offset).limit(limit).all()

    def count_announcements(
        self,
        db: Session,
        audience_filter: Optional[List[str]] = None,
        department_id: Optional[str] = None,
        status: Optional[str] = "published",
    ) -> int:
        """Counts announcements matching audience and status filters."""
        query = db.query(func.count(Announcement.id))
        if status:
            query = query.filter(Announcement.status == status)
        if audience_filter:
            query = query.filter(or_(
                Announcement.audience.in_(audience_filter),
                Announcement.audience == "all"
            ))
        if department_id:
            query = query.filter(or_(
                Announcement.department_id == department_id,
                Announcement.department_id.is_(None)
            ))
        return query.scalar() or 0

    def update_announcement(self, db: Session, announcement_id: str, updates: Dict[str, Any]) -> Optional[Announcement]:
        """Updates an existing announcement."""
        ann = self.get_announcement_by_id(db, announcement_id)
        if not ann:
            return None
        for k, v in updates.items():
            if hasattr(ann, k) and v is not None:
                setattr(ann, k, v)
        db.commit()
        db.refresh(ann)
        return ann

    def delete_announcement(self, db: Session, announcement_id: str) -> bool:
        """Deletes an announcement."""
        ann = self.get_announcement_by_id(db, announcement_id)
        if not ann:
            return False
        db.delete(ann)
        db.commit()
        return True


announcement_repository = AnnouncementRepository()
