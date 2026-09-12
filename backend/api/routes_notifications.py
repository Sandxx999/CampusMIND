"""Versioned API Router for Phase 7 System Alerts & Notifications.

Mounted under /api/v1/notifications
Provides user notification listing and status updates.
"""
from typing import Optional
from fastapi import APIRouter, Depends
from auth.rbac import get_current_user
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
