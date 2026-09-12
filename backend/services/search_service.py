"""Unified Search Service for CampusMIND 2.0.

Provides authorization-filtered unified institutional search across courses, announcements, campus events, and documents.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy import or_
from db.session import get_db_session
from db.models import Course, Announcement, CampusEvent, KnowledgeDocument
from models.schemas import UserSchema


class SearchService:
    def search_institutional_records(
        self,
        user: UserSchema,
        query: str,
        limit_per_category: int = 5,
    ) -> Dict[str, Any]:
        """
        Executes unified institutional search across domain entities.
        Strictly applies server-side role and audience security filters.
        """
        if not query or len(query.strip()) < 2:
            return {
                "query": query,
                "courses": [],
                "announcements": [],
                "events": [],
                "documents": [],
            }

        q_pattern = f"%{query.strip()}%"

        audience_filter = ["all"]
        if user.role == "student":
            audience_filter.append("students")
        elif user.role == "faculty":
            audience_filter.extend(["faculty", "students"])
        elif user.role == "admin":
            audience_filter.extend(["admin", "faculty", "students"])

        with get_db_session() as session:
            # 1. Search Courses
            courses = session.query(Course).filter(
                or_(
                    Course.code.ilike(q_pattern),
                    Course.title.ilike(q_pattern)
                )
            ).limit(limit_per_category).all()

            course_results = [
                {
                    "type": "course",
                    "id": c.id,
                    "code": c.code,
                    "title": c.title,
                    "credits": c.credits,
                    "department_name": c.department.name if c.department else None,
                }
                for c in courses
            ]

            # 2. Search Announcements (Audience Filtered)
            announcements = session.query(Announcement).filter(
                Announcement.status == "published",
                or_(
                    Announcement.audience.in_(audience_filter),
                    Announcement.audience == "all"
                ),
                or_(
                    Announcement.title.ilike(q_pattern),
                    Announcement.content.ilike(q_pattern)
                )
            ).order_by(Announcement.created_at.desc()).limit(limit_per_category).all()

            announcement_results = [
                {
                    "type": "announcement",
                    "id": a.id,
                    "title": a.title,
                    "snippet": a.content[:150] + "..." if len(a.content) > 150 else a.content,
                    "priority": a.priority,
                    "created_at": a.created_at.isoformat() if hasattr(a.created_at, "isoformat") else str(a.created_at),
                }
                for a in announcements
            ]

            # 3. Search Campus Events (Audience Filtered)
            events = session.query(CampusEvent).filter(
                CampusEvent.status == "scheduled",
                or_(
                    CampusEvent.audience.in_(audience_filter),
                    CampusEvent.audience == "all"
                ),
                or_(
                    CampusEvent.title.ilike(q_pattern),
                    CampusEvent.description.ilike(q_pattern),
                    CampusEvent.location.ilike(q_pattern)
                )
            ).order_by(CampusEvent.start_time.asc()).limit(limit_per_category).all()

            event_results = [
                {
                    "type": "event",
                    "id": e.id,
                    "title": e.title,
                    "location": e.location,
                    "start_time": e.start_time.isoformat() if hasattr(e.start_time, "isoformat") else str(e.start_time),
                    "category": e.category,
                }
                for e in events
            ]

            # 4. Search Knowledge Documents (Audience Filtered)
            docs = session.query(KnowledgeDocument).filter(
                KnowledgeDocument.is_active == True,
                or_(
                    KnowledgeDocument.audience.in_(audience_filter),
                    KnowledgeDocument.audience == "all"
                ),
                or_(
                    KnowledgeDocument.title.ilike(q_pattern),
                    KnowledgeDocument.category.ilike(q_pattern),
                    KnowledgeDocument.file_path.ilike(q_pattern)
                )
            ).limit(limit_per_category).all()

            doc_results = [
                {
                    "type": "document",
                    "id": d.id,
                    "title": d.title,
                    "category": d.category,
                    "file_path": d.file_path,
                }
                for d in docs
            ]

            return {
                "query": query,
                "courses": course_results,
                "announcements": announcement_results,
                "events": event_results,
                "documents": doc_results,
            }


search_service = SearchService()
