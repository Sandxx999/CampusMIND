"""Event Service for CampusMIND 2.0.

Implements business logic for campus events and registrations.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from db.session import get_db_session
from db.models import User, CampusEvent
from models.schemas import UserSchema
from repositories.event_repository import event_repository
from repositories.audit_repository import audit_repository


class EventService:
    def create_event(self, user: UserSchema, data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new campus event. Restricted to Faculty and Admin."""
        if user.role == "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students are not authorized to create campus events."
            )

        start_time = data.get("start_time")
        end_time = data.get("end_time")

        if isinstance(start_time, str):
            try:
                start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            except ValueError:
                start_time = datetime.now()
        elif not start_time:
            start_time = datetime.now()

        if isinstance(end_time, str):
            try:
                end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            except ValueError:
                end_time = start_time
        elif not end_time:
            end_time = start_time

        with get_db_session() as session:
            actor = session.query(User).filter(User.username == user.username).first()
            event_data = {
                "title": data["title"],
                "description": data["description"],
                "location": data["location"],
                "start_time": start_time,
                "end_time": end_time,
                "organizer_id": actor.id if actor else "usr_admin1",
                "audience": data.get("audience", "all"),
                "department_id": data.get("department_id"),
                "category": data.get("category", "general"),
                "capacity": data.get("capacity"),
                "requires_registration": data.get("requires_registration", False),
                "status": data.get("status", "scheduled"),
            }
            evt = event_repository.create_event(session, event_data)

            audit_repository.log_audit_event(
                event_type="EVENT_CREATED",
                actor_username=user.username,
                user_id=actor.id if actor else None,
                details=f"Created campus event '{evt.title}' (ID: {evt.id})"
            )

            return {
                "id": evt.id,
                "title": evt.title,
                "description": evt.description,
                "location": evt.location,
                "start_time": evt.start_time.isoformat() if hasattr(evt.start_time, "isoformat") else str(evt.start_time),
                "end_time": evt.end_time.isoformat() if hasattr(evt.end_time, "isoformat") else str(evt.end_time),
                "organizer_name": actor.display_name if actor else None,
                "audience": evt.audience,
                "category": evt.category,
                "capacity": evt.capacity,
                "requires_registration": evt.requires_registration,
                "status": evt.status,
            }


    def list_events(
        self,
        user: UserSchema,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Lists campus events matching role audience."""
        audience_filter = ["all"]
        if user.role == "student":
            audience_filter.append("students")
        elif user.role == "faculty":
            audience_filter.extend(["faculty", "students"])
        elif user.role == "admin":
            audience_filter.extend(["admin", "faculty", "students"])

        with get_db_session() as session:
            events = event_repository.list_events(
                session,
                audience_filter=audience_filter,
                category=category,
                status="scheduled",
                limit=limit,
                offset=offset,
            )
            total = event_repository.count_events(
                session,
                audience_filter=audience_filter,
                category=category,
                status="scheduled",
            )

            results = [
                {
                    "id": e.id,
                    "title": e.title,
                    "description": e.description,
                    "location": e.location,
                    "start_time": e.start_time.isoformat() if hasattr(e.start_time, "isoformat") else str(e.start_time),
                    "end_time": e.end_time.isoformat() if hasattr(e.end_time, "isoformat") else str(e.end_time),
                    "organizer_name": e.organizer.display_name if e.organizer else None,
                    "category": e.category,
                    "capacity": e.capacity,
                    "requires_registration": e.requires_registration,
                    "status": e.status,
                }
                for e in events
            ]

            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "events": results,
            }

    def register_for_event(self, user: UserSchema, event_id: str) -> Dict[str, Any]:
        """Registers the authenticated user for a campus event."""
        with get_db_session() as session:
            actor = session.query(User).filter(User.username == user.username).first()
            if not actor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User record not found."
                )

            reg = event_repository.register_user(session, event_id, actor.id)
            if not reg:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Campus event '{event_id}' not found."
                )

            return {
                "message": "Successfully registered for event.",
                "event_id": event_id,
                "status": reg.status,
            }


event_service = EventService()
