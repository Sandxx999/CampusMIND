"""Versioned API Router for Phase 7 System Alerts & Notifications.

Mounted under /api/v1/notifications
Provides user notification listing and status updates.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials
from auth.rbac import get_current_user, security
from auth.jwt_handler import decode_access_token
from models.schemas import (
    UserSchema,
    NotificationAlertListResponse,
    NotificationMarkReadRequest,
)
from services.intervention_service import intervention_service

router_v1 = APIRouter(prefix="/api/v1/notifications", tags=["Phase 7 Notifications"])


@router_v1.get("", response_model=NotificationAlertListResponse)
def list_notifications(
    unread_only: bool = False,
    current_user: UserSchema = Depends(get_current_user),
):
    """Lists system alerts and notifications for the authenticated user."""
    return intervention_service.list_notifications(
        current_user=current_user,
        unread_only=unread_only,
    )


@router_v1.post("/mark-read")
def mark_notifications_read(
    body: NotificationMarkReadRequest,
    current_user: UserSchema = Depends(get_current_user),
):
    """Marks specified notifications as read for the authenticated user."""
    return intervention_service.mark_notifications_read(
        current_user=current_user,
        notification_ids=body.notification_ids,
    )


@router_v1.get("/stream")
async def stream_notifications(
    token: Optional[str] = Query(None, description="JWT access token for EventSource authentication"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """
    Server-Sent Events (SSE) real-time notification stream for the authenticated user.
    Enforces server-side identity verification via token.
    """
    raw_token = token or (credentials.credentials if credentials else None)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is required for notification stream.",
        )

    payload = decode_access_token(raw_token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token for notification stream.",
        )

    # Get DB user ID for authenticated subject
    from db.session import get_db_session
    from db.models import User
    with get_db_session() as session:
        user_rec = session.query(User).filter(User.username == payload["sub"]).first()
        if not user_rec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User account record not found.",
            )
        target_user_id = user_rec.id

    from core.notifications import notification_transport
    return StreamingResponse(
        notification_transport.stream_user_events(target_user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

