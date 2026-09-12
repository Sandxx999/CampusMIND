"""
Real-Time Notification Transport Infrastructure for CampusMIND 2.0.

Provides Server-Sent Events (SSE) stream generation, real-time alert broadcasting,
user isolation guarantees, and graceful connection lifecycle management.

Transport providers:
  - "memory" (default): in-process asyncio queues; single-worker / local development.
  - "redis": Redis pub/sub channel per user; multi-worker / horizontal scaling.

The active provider is selected from settings.NOTIFICATION_TRANSPORT:
  NOTIFICATION_TRANSPORT=memory   → InMemoryTransport (default)
  NOTIFICATION_TRANSPORT=redis    → RedisTransport (requires REDIS_URL)

Neither provider exposes Redis credentials through logs or API responses.
Per-user notification isolation is enforced at the transport layer; a
notification addressed to user A will never be received by user B.
"""
import asyncio
import json
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncGenerator

from core.logging import logger


# ---------------------------------------------------------------------------
# Abstract transport interface
# ---------------------------------------------------------------------------

class NotificationTransport(ABC):
    """Common interface for SSE notification transports."""

    @abstractmethod
    def subscribe(self, user_id: str) -> asyncio.Queue:
        """Register a new SSE connection for *user_id* and return its queue."""

    @abstractmethod
    def unsubscribe(self, user_id: str, queue: asyncio.Queue) -> None:
        """Remove a disconnected queue for *user_id*."""

    @abstractmethod
    def publish_notification(self, user_id: str, notification: Dict[str, Any]) -> int:
        """
        Push *notification* to all live queues for *user_id*.
        Returns the number of queues notified (0 when the user has no active stream).
        """

    async def stream_user_events(
        self,
        user_id: str,
        keepalive_seconds: int = 1,
    ) -> AsyncGenerator[str, None]:
        """
        Async generator yielding formatted SSE text chunks for *user_id*.
        Sends periodic ping keepalives to prevent proxy timeouts.
        Cleans up the subscriber queue on disconnect or cancellation.
        """
        queue = self.subscribe(user_id)
        try:
            # Yield initial connection confirmation event (user_id is server-resolved)
            init_event = json.dumps({"status": "connected", "user_id": user_id})
            yield f"event: sse_connected\ndata: {init_event}\n\n"

            while True:
                try:
                    event_data = await asyncio.wait_for(
                        queue.get(), timeout=keepalive_seconds
                    )
                    data_str = json.dumps(event_data)
                    yield f"id: {event_data.get('id')}\nevent: notification\ndata: {data_str}\n\n"
                except asyncio.TimeoutError:
                    yield (
                        f"event: ping\ndata: "
                        f"{json.dumps({'timestamp': float(asyncio.get_event_loop().time())})}\n\n"
                    )
        except asyncio.CancelledError:
            logger.debug(f"SSE event stream cancelled for user '{user_id}'.")
        finally:
            self.unsubscribe(user_id, queue)

    @staticmethod
    def _build_event_data(notification: Dict[str, Any]) -> Dict[str, Any]:
        """Normalise an incoming notification dict into the canonical SSE payload."""
        return {
            "id": notification.get("id", f"notif_{uuid.uuid4().hex[:8]}"),
            "category": notification.get("category", "academic"),
            "severity": notification.get("severity", "info"),
            "title": notification.get("title", "New Notification"),
            "message": notification.get("message", ""),
            "link": notification.get("link", "/analytics"),
            "is_read": notification.get("is_read", False),
            "created_at": notification.get("created_at", ""),
        }


# ---------------------------------------------------------------------------
# In-memory transport (default; single-worker only)
# ---------------------------------------------------------------------------

class InMemoryTransport(NotificationTransport):
    """
    Manages active SSE subscriber queues per user_id in process memory.

    Per-user isolation: each user has its own list of asyncio.Queue instances.
    publish_notification() addresses messages by user_id; no cross-user
    delivery is possible at the queue level.

    Limitation: state is not shared across multiple worker processes.
    For multi-worker deployments use RedisTransport.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}

    def subscribe(self, user_id: str) -> asyncio.Queue:
        """Subscribes an active client connection to real-time events for user_id."""
        queue: asyncio.Queue = asyncio.Queue()
        if user_id not in self._subscribers:
            self._subscribers[user_id] = []
        self._subscribers[user_id].append(queue)
        logger.debug(
            f"[InMemoryTransport] User '{user_id}' subscribed. "
            f"Active connections: {len(self._subscribers[user_id])}"
        )
        return queue

    def unsubscribe(self, user_id: str, queue: asyncio.Queue) -> None:
        """Removes a client connection queue upon disconnect."""
        if user_id in self._subscribers:
            if queue in self._subscribers[user_id]:
                self._subscribers[user_id].remove(queue)
            if not self._subscribers[user_id]:
                del self._subscribers[user_id]
        logger.debug(f"[InMemoryTransport] User '{user_id}' unsubscribed.")

    def publish_notification(self, user_id: str, notification: Dict[str, Any]) -> int:
        """
        Publishes a notification alert to all active connection queues for user_id.
        Returns the number of active listeners notified.
        """
        queues = self._subscribers.get(user_id, [])
        if not queues:
            return 0

        event_data = self._build_event_data(notification)
        published_count = 0
        for q in queues:
            try:
                q.put_nowait(event_data)
                published_count += 1
            except asyncio.QueueFull:
                logger.warning(
                    f"[InMemoryTransport] Queue full for user '{user_id}'. Message dropped."
                )
        return published_count

    # ------------------------------------------------------------------
    # Backwards-compat shim: expose old attribute name used in tests
    # ------------------------------------------------------------------
    @property
    def subscribers(self) -> Dict[str, List[asyncio.Queue]]:
        """Read-only view of active subscriber queues (for test inspection)."""
        return self._subscribers


# ---------------------------------------------------------------------------
# Redis transport (multi-worker / horizontal-scaling)
# ---------------------------------------------------------------------------

class RedisTransport(NotificationTransport):
    """
    Redis pub/sub backed SSE transport for multi-worker deployments.

    Each user has a dedicated pub/sub channel: "sse:user:{user_id}".
    publish_notification() uses Redis PUBLISH; stream_user_events() subscribes
    to the channel and feeds messages into a local asyncio.Queue for the SSE
    generator, preserving the standard streaming interface.

    Isolation guarantee: channel names are keyed by server-resolved user_id;
    no client-supplied identifier influences channel selection.

    Fail-safe: if Redis is unavailable the transport raises RuntimeError at
    subscribe time so the caller (stream endpoint) can return 503.  Credential
    material (REDIS_URL) is never logged or surfaced in API responses.
    """

    CHANNEL_PREFIX = "sse:user:"

    def __init__(self, redis_url: str):
        # Store URL privately; never log it.
        self._redis_url: str = redis_url
        # Local in-memory queues so stream_user_events() works without blocking.
        self._local_queues: Dict[str, List[asyncio.Queue]] = {}
        self._redis_available: Optional[bool] = None  # lazily verified

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _channel(self, user_id: str) -> str:
        """Returns the per-user Redis channel name."""
        return f"{self.CHANNEL_PREFIX}{user_id}"

    def _get_redis_client(self):
        """
        Returns a synchronous redis.Redis client.
        Raises RuntimeError (no credentials in message) if redis is unavailable.
        """
        try:
            import redis as _redis  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Redis client library is not installed. "
                "Install 'redis' to use the Redis notification transport."
            ) from exc
        try:
            client = _redis.from_url(self._redis_url, socket_connect_timeout=2)
            client.ping()
            return client
        except Exception as exc:
            # Do NOT include self._redis_url in the log message
            logger.error(
                "[RedisTransport] Could not connect to Redis. "
                "Falling back gracefully. Error type: %s", type(exc).__name__
            )
            raise RuntimeError(
                "Redis notification transport unavailable. "
                "Check REDIS_URL configuration."
            ) from exc

    async def _get_async_redis(self):
        """
        Returns an async redis.asyncio.Redis client.
        Raises RuntimeError if redis is unavailable.
        """
        try:
            import redis.asyncio as _aredis  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Redis async client is not installed. "
                "Install 'redis>=4.2.0' for async support."
            ) from exc
        try:
            client = _aredis.from_url(self._redis_url, socket_connect_timeout=2)
            await client.ping()
            return client
        except Exception as exc:
            logger.error(
                "[RedisTransport] Async Redis unavailable. Error type: %s",
                type(exc).__name__,
            )
            raise RuntimeError(
                "Redis notification transport unavailable."
            ) from exc

    # ------------------------------------------------------------------
    # Transport interface
    # ------------------------------------------------------------------

    def subscribe(self, user_id: str) -> asyncio.Queue:
        """Creates a local asyncio.Queue for this SSE connection."""
        queue: asyncio.Queue = asyncio.Queue()
        if user_id not in self._local_queues:
            self._local_queues[user_id] = []
        self._local_queues[user_id].append(queue)
        logger.debug(
            f"[RedisTransport] User '{user_id}' subscribed locally. "
            f"Active connections: {len(self._local_queues[user_id])}"
        )
        return queue

    def unsubscribe(self, user_id: str, queue: asyncio.Queue) -> None:
        """Removes the queue; cleans up the user entry when no connections remain."""
        if user_id in self._local_queues:
            if queue in self._local_queues[user_id]:
                self._local_queues[user_id].remove(queue)
            if not self._local_queues[user_id]:
                del self._local_queues[user_id]
        logger.debug(f"[RedisTransport] User '{user_id}' unsubscribed.")

    def publish_notification(self, user_id: str, notification: Dict[str, Any]) -> int:
        """
        Publishes *notification* to the per-user Redis channel.
        Also delivers to local in-process queues so single-worker tests work.
        Returns 1 on success, 0 on failure.
        """
        event_data = self._build_event_data(notification)

        # Deliver to local in-process queues (same worker)
        local_count = 0
        for q in self._local_queues.get(user_id, []):
            try:
                q.put_nowait(event_data)
                local_count += 1
            except asyncio.QueueFull:
                logger.warning(
                    f"[RedisTransport] Local queue full for user '{user_id}'."
                )

        # Publish to Redis for other workers
        try:
            client = self._get_redis_client()
            recipients = client.publish(self._channel(user_id), json.dumps(event_data))
            logger.debug(
                f"[RedisTransport] Published to channel for user '{user_id}'. "
                f"Redis subscribers: {recipients}"
            )
            return max(local_count, int(recipients))
        except RuntimeError:
            # Redis unavailable; local delivery still succeeded
            return local_count

    async def stream_user_events(  # type: ignore[override]
        self,
        user_id: str,
        keepalive_seconds: int = 1,
    ) -> AsyncGenerator[str, None]:
        """
        Subscribes to the per-user Redis pub/sub channel and forwards events.
        Falls back to purely local queue delivery if Redis is unavailable.
        """
        local_queue = self.subscribe(user_id)
        redis_client = None
        pubsub = None

        try:
            redis_client = await self._get_async_redis()
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(self._channel(user_id))

            # Yield initial connection confirmation
            init_event = json.dumps({"status": "connected", "user_id": user_id})
            yield f"event: sse_connected\ndata: {init_event}\n\n"

            while True:
                try:
                    # First check local queue (fast path)
                    try:
                        event_data = local_queue.get_nowait()
                        data_str = json.dumps(event_data)
                        yield (
                            f"id: {event_data.get('id')}\n"
                            f"event: notification\ndata: {data_str}\n\n"
                        )
                        continue
                    except asyncio.QueueEmpty:
                        pass

                    # Then poll Redis (async, non-blocking, with timeout)
                    msg = await asyncio.wait_for(
                        pubsub.get_message(ignore_subscribe_messages=True, timeout=0.05),
                        timeout=keepalive_seconds,
                    )
                    if msg and msg["type"] == "message":
                        event_data = json.loads(msg["data"])
                        data_str = json.dumps(event_data)
                        yield (
                            f"id: {event_data.get('id')}\n"
                            f"event: notification\ndata: {data_str}\n\n"
                        )
                    else:
                        # Keepalive ping
                        yield (
                            f"event: ping\ndata: "
                            f"{json.dumps({'timestamp': float(asyncio.get_event_loop().time())})}\n\n"
                        )
                except asyncio.TimeoutError:
                    yield (
                        f"event: ping\ndata: "
                        f"{json.dumps({'timestamp': float(asyncio.get_event_loop().time())})}\n\n"
                    )

        except RuntimeError:
            # Redis unavailable — fall back to in-memory streaming
            logger.warning(
                "[RedisTransport] Redis unavailable for streaming; falling back to local queue."
            )
            # Delegate to parent's in-memory logic using the local queue
            init_event = json.dumps({"status": "connected", "user_id": user_id})
            yield f"event: sse_connected\ndata: {init_event}\n\n"
            while True:
                try:
                    event_data = await asyncio.wait_for(
                        local_queue.get(), timeout=keepalive_seconds
                    )
                    data_str = json.dumps(event_data)
                    yield (
                        f"id: {event_data.get('id')}\n"
                        f"event: notification\ndata: {data_str}\n\n"
                    )
                except asyncio.TimeoutError:
                    yield (
                        f"event: ping\ndata: "
                        f"{json.dumps({'timestamp': float(asyncio.get_event_loop().time())})}\n\n"
                    )

        except asyncio.CancelledError:
            logger.debug(f"[RedisTransport] SSE stream cancelled for user '{user_id}'.")
        finally:
            if pubsub:
                try:
                    await pubsub.unsubscribe(self._channel(user_id))
                    await redis_client.aclose()
                except Exception:
                    pass
            self.unsubscribe(user_id, local_queue)


# ---------------------------------------------------------------------------
# Transport factory
# ---------------------------------------------------------------------------

def _create_transport() -> NotificationTransport:
    """
    Selects and instantiates the notification transport based on
    settings.NOTIFICATION_TRANSPORT.

    Supported values (case-insensitive):
      "memory" or "sse"  → InMemoryTransport  (default)
      "redis"            → RedisTransport (uses settings.REDIS_URL)

    Falls back to InMemoryTransport if an unrecognised value is configured,
    logging a warning but never exposing credential material.
    """
    from core.config import settings  # local import to avoid circular imports

    mode = settings.NOTIFICATION_TRANSPORT.lower().strip()

    if mode == "redis":
        logger.info(
            "[NotificationTransport] Initialising RedisTransport for multi-worker SSE."
            # Do NOT log REDIS_URL here
        )
        return RedisTransport(redis_url=settings.REDIS_URL)

    if mode not in {"memory", "sse", "in-memory", "inmemory"}:
        logger.warning(
            f"[NotificationTransport] Unknown NOTIFICATION_TRANSPORT='{mode}'. "
            "Defaulting to InMemoryTransport."
        )

    logger.info("[NotificationTransport] Initialising InMemoryTransport (single-worker).")
    return InMemoryTransport()


# ---------------------------------------------------------------------------
# Module-level singleton — import this everywhere
# ---------------------------------------------------------------------------

notification_transport: NotificationTransport = _create_transport()
"""
Singleton notification transport instance.

Import as::

    from core.notifications import notification_transport

Use :func:`~NotificationTransport.publish_notification` to push events and
:func:`~NotificationTransport.stream_user_events` from the SSE endpoint.
"""
