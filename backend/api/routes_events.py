"""Campus Events API Routes for CampusMIND 2.0.

Exposes endpoints for campus events and registrations under /api/v1/events.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from auth.rbac import get_current_user, require_role
from models.schemas import (
    EventCreateRequest,
    CampusEventSchema,
    EventListResponse,
    UserSchema,
)
from services.event_service import event_service

router_v1 = APIRouter(prefix="/api/v1/events", tags=["Campus Events"])


@router_v1.get("", response_model=EventListResponse)
def list_events(
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: UserSchema = Depends(get_current_user),
):
    """Lists campus events matching role audience."""
    return event_service.list_events(
        user=user,
        category=category,
        limit=limit,
        offset=offset,
    )


@router_v1.post("", response_model=CampusEventSchema)
def create_event(
    req: EventCreateRequest,
    user: UserSchema = Depends(require_role(["faculty", "admin"])),
):
    """Creates a new campus event. Restricted to Faculty and Admin."""
    return event_service.create_event(user, req.model_dump())


@router_v1.post("/{event_id}/register")
def register_for_event(
    event_id: str,
    user: UserSchema = Depends(get_current_user),
):
    """Registers the authenticated user for a campus event."""
    return event_service.register_for_event(user=user, event_id=event_id)
