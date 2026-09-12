"""Event Repository for CampusMIND 2.0.

Provides database access for campus events and registrations.
"""
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from db.models import CampusEvent, EventRegistration, User


class EventRepository:
    def create_event(self, db: Session, data: Dict[str, Any]) -> CampusEvent:
        """Creates a new campus event."""
        event = CampusEvent(
            id=data.get("id", f"evt_{uuid.uuid4().hex[:12]}"),
            title=data["title"],
            description=data["description"],
            location=data["location"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            organizer_id=data["organizer_id"],
            audience=data.get("audience", "all"),
            department_id=data.get("department_id"),
            category=data.get("category", "general"),
            capacity=data.get("capacity"),
            requires_registration=data.get("requires_registration", False),
            status=data.get("status", "scheduled"),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    def get_event_by_id(self, db: Session, event_id: str) -> Optional[CampusEvent]:
        """Retrieves a campus event by ID."""
        return db.query(CampusEvent).filter(CampusEvent.id == event_id).first()

    def list_events(
        self,
        db: Session,
        audience_filter: Optional[List[str]] = None,
        category: Optional[str] = None,
        status: Optional[str] = "scheduled",
        limit: int = 50,
        offset: int = 0,
    ) -> List[CampusEvent]:
        """Lists campus events matching filters."""
        query = db.query(CampusEvent)
        if status:
            query = query.filter(CampusEvent.status == status)
        if category:
            query = query.filter(CampusEvent.category == category)
        if audience_filter:
            query = query.filter(or_(
                CampusEvent.audience.in_(audience_filter),
                CampusEvent.audience == "all"
            ))
        return query.order_by(CampusEvent.start_time.asc()).offset(offset).limit(limit).all()

    def count_events(
        self,
        db: Session,
        audience_filter: Optional[List[str]] = None,
        category: Optional[str] = None,
        status: Optional[str] = "scheduled",
    ) -> int:
        """Counts campus events matching filters."""
        query = db.query(func.count(CampusEvent.id))
        if status:
            query = query.filter(CampusEvent.status == status)
        if category:
            query = query.filter(CampusEvent.category == category)
        if audience_filter:
            query = query.filter(or_(
                CampusEvent.audience.in_(audience_filter),
                CampusEvent.audience == "all"
            ))
        return query.scalar() or 0

    def register_user(self, db: Session, event_id: str, user_id: str) -> Optional[EventRegistration]:
        """Registers a user for a campus event."""
        event = self.get_event_by_id(db, event_id)
        if not event:
            return None

        existing = db.query(EventRegistration).filter(
            EventRegistration.event_id == event_id,
            EventRegistration.user_id == user_id
        ).first()
        if existing:
            return existing

        reg = EventRegistration(
            id=f"reg_{uuid.uuid4().hex[:12]}",
            event_id=event_id,
            user_id=user_id,
            status="registered",
        )
        db.add(reg)
        db.commit()
        db.refresh(reg)
        return reg

    def get_user_registrations(self, db: Session, user_id: str) -> List[EventRegistration]:
        """Retrieves event registrations for a user."""
        return db.query(EventRegistration).filter(EventRegistration.user_id == user_id).all()


event_repository = EventRepository()
