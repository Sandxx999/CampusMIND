"""
Real-Time Notification Transport Infrastructure for CampusMIND 2.0.

Provides Server-Sent Events (SSE) stream generation, real-time alert broadcasting,
user isolation guarantees, and graceful connection lifecycle management.
"""
import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional, AsyncGenerator
from core.logging import logger


class NotificationTransportManager:
    """
    Manages active SSE subscriber queues per user_id, ensuring
    strict real-time user isolation and reliable message publishing.
    """

    def __init__(self):
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}

    def subscribe(self, user_id: str) -> asyncio.Queue:
        """Subscribes an active client connection to real-time events for user_id."""
        queue: asyncio.Queue = asyncio.Queue()
        if user_id not in self.subscribers:
            self.subscribers[user_id] = []
        self.subscribers[user_id].append(queue)
        logger.debug(f"User '{user_id}' subscribed to SSE notification stream. Active connections: {len(self.subscribers[user_id])}")
        return queue

    def unsubscribe(self, user_id: str, queue: asyncio.Queue) -> None:
        """Removes a client connection queue upon disconnect."""
        if user_id in self.subscribers:
            if queue in self.subscribers[user_id]:
                self.subscribers[user_id].remove(queue)
            if not self.subscribers[user_id]:
                del self.subscribers[user_id]
        logger.debug(f"User '{user_id}' unsubscribed from SSE notification stream.")

    def publish_notification(self, user_id: str, notification: Dict[str, Any]) -> int:
        """
        Publishes a notification alert to all active connection queues for user_id.
        Returns the number of active listeners notified.
        """
        queues = self.subscribers.get(user_id, [])
        if not queues:
            return 0

        event_data = {
            "id": notification.get("id", f"notif_{uuid.uuid4().hex[:8]}"),
            "category": notification.get("category", "academic"),
            "severity": notification.get("severity", "info"),
            "title": notification.get("title", "New Notification"),
            "message": notification.get("message", ""),
            "link": notification.get("link", "/analytics"),
            "is_read": notification.get("is_read", False),
            "created_at": notification.get("created_at", ""),
        }

        published_count = 0
        for q in queues:
            try:
                q.put_nowait(event_data)
                published_count += 1
            except asyncio.QueueFull:
                logger.warning(f"Notification queue full for user '{user_id}'. Skipping message drop.")

        return published_count

    async def stream_user_events(
        self,
        user_id: str,
        keepalive_seconds: int = 1,
    ) -> AsyncGenerator[str, None]:

        """
        Async generator yielding formatted SSE text chunks ('event: notification\\ndata: {...}\\n\\n')
        with periodic ping keepalives to prevent proxy timeouts.
        """
        queue = self.subscribe(user_id)
        try:
            # Yield initial connection confirmation event
            init_event = json.dumps({"status": "connected", "user_id": user_id})
            yield f"event: sse_connected\ndata: {init_event}\n\n"

            while True:
                try:
                    event_data = await asyncio.wait_for(queue.get(), timeout=keepalive_seconds)
                    data_str = json.dumps(event_data)
                    yield f"id: {event_data.get('id')}\nevent: notification\ndata: {data_str}\n\n"
                except asyncio.TimeoutError:
                    # Send periodic keepalive ping
                    yield f"event: ping\ndata: {json.dumps({'timestamp': float(asyncio.get_event_loop().time())})}\n\n"
        except asyncio.CancelledError:
            logger.debug(f"SSE event stream cancelled for user '{user_id}'.")
        finally:
            self.unsubscribe(user_id, queue)


notification_transport = NotificationTransportManager()
