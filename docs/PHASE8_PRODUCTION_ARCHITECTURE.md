# CampusMIND 2.0 — Phase 8: Production Scalability, Observability & Real-Time Infrastructure

> **Branch:** `campusmind-2.0`
> **Phase Gate:** Phases 0–7 passed ✅ (113/113 tests, clean working tree, SAFE TO PROCEED)
> **Phase 8 Baseline:** `b4efd6b` — Build Phase 7 intelligent academic interventions and notifications

---

## Overview

Phase 8 delivers the production-readiness and operational layer required to run CampusMIND 2.0 safely at scale. It adds four orthogonal capabilities without weakening any Phase 0–7 security invariant:

| Capability | Component |
|---|---|
| Distributed background task infrastructure | `backend/core/tasks.py` |
| Real-time SSE notification transport | `backend/core/notifications.py` |
| Structured observability & health probes | `backend/api/routes_system.py`, `backend/core/middleware.py` |
| Secret-safe structured logging | `backend/core/logging.py` |

---

## 1. Distributed Background Task Infrastructure

### Architecture

`BackgroundTaskManager` (`backend/core/tasks.py`) provides a **provider-agnostic execution abstraction** over three worker backends:

| Provider (`TASK_QUEUE_PROVIDER`) | Execution Strategy | Use Case |
|---|---|---|
| `inline` / `sync` / `test` | Synchronous, same thread | Tests, CI, debugging |
| `threaded` (default) | `threading.Thread`, daemon | Single-server deployments |
| `redis` / `distributed` | Thread (falls back gracefully if Redis unavailable) | Multi-instance horizontal scaling |

All task lifecycle state is persisted to the `system_tasks` table via `SystemTaskRepository`.

### Task State Machine

```
QUEUED → RUNNING → COMPLETED
                 ↘ FAILED
```

Every transition writes a timestamped row to `system_tasks`, enabling audit trails and retry logic.

### Key Guarantees

- **Deduplication:** By default (`allow_duplicate=False`), submitting a second task of the same `task_type` while one is active returns the existing task rather than creating a duplicate.
- **Error sanitization:** Failed-task `details` field records only `Task failed: <ExceptionType>` — never a full stack trace or credential — preventing secret leakage into the database.
- **Retry:** `retry_task()` forces `allow_duplicate=True`, enabling safe re-submission without deduplication collision.
- **Observability:** Every state change emits a structured log line with `task_id`, `task_type`, and duration.

### Configuration

```env
TASK_QUEUE_PROVIDER=threaded   # inline | threaded | redis
REDIS_URL=redis://localhost:6379/0
```

---

## 2. Real-Time SSE Notification Transport

### Architecture

`NotificationTransportManager` (`backend/core/notifications.py`) maintains an in-process subscriber registry keyed by `user_id`:

```
User Browser ─── GET /api/v1/notifications/stream?token=<jwt> ───► FastAPI
                                                                       │
                                   asyncio.Queue (per connection) ◄────┘
                                          │
                   publish_notification() ─────► put_nowait → queue
```

### User Isolation

Each `subscribe()` call creates a **new, separate `asyncio.Queue`** for the given `user_id`. `publish_notification(user_id, ...)` delivers exclusively to queues registered under that `user_id` — it is structurally impossible to deliver a message to a different user's queue.

### SSE Stream Protocol

Each yielded chunk follows the W3C Server-Sent Events specification:

```
event: sse_connected
data: {"status": "connected", "user_id": "<id>"}

id: <notification_id>
event: notification
data: {"category": "...", "severity": "...", "title": "...", "message": "...", ...}

event: ping
data: {"timestamp": <float>}
```

- **Connection confirmation** (`sse_connected`) is emitted immediately so the client can confirm authentication succeeded.
- **Keepalive pings** fire on `asyncio.TimeoutError` (default: every 1 second in test, configurable for production) to prevent proxy/load-balancer timeouts.
- **Graceful cleanup**: `finally` in `stream_user_events` always calls `unsubscribe()`, preventing queue leaks on client disconnect.

### Authentication

The SSE stream endpoint (`/api/v1/notifications/stream`) accepts the JWT via:

1. `?token=<jwt>` query parameter (for SSE clients that cannot set headers)
2. `Authorization: Bearer <jwt>` header

Unauthenticated or invalid-token requests receive `HTTP 401` before the stream is opened.

### Configuration

```env
NOTIFICATION_TRANSPORT=sse   # sse | (future: websocket | pubsub)
```

---

## 3. Structured Observability & Health Probes

### Endpoints

All health routes are mounted at both `/health/*` (bare) and `/api/v1/health/*` (versioned) paths.

| Endpoint | Purpose | Auth Required |
|---|---|---|
| `GET /health` | Overall operational status | No |
| `GET /health/liveness` | Process liveness (no external checks) | No |
| `GET /health/readiness` | Dependency readiness (DB required) | No |
| `GET /health/dependencies` | Detailed per-dependency status map | No |

### Probe Semantics

**Liveness** (`/health/liveness`): Returns `200 alive` as long as the Python process is running. Never checks external systems. Intended for container restart orchestration (e.g., Kubernetes `livenessProbe`).

**Readiness** (`/health/readiness`): Checks:
- Database (`SELECT 1` via `check_database_health()`)
- ChromaDB directory presence
- Task queue (Redis ping if provider is `redis`)

Returns `HTTP 503` if the database is unhealthy, indicating the pod should not receive traffic. Intended for Kubernetes `readinessProbe` / load-balancer health checks.

**Dependencies** (`/health/dependencies`): Returns a structured JSON map of all dependency statuses without exposing connection strings, credentials, or internal stack traces.

```json
{
  "status": "healthy",
  "dependencies": {
    "database": {"healthy": true, "status": "connected"},
    "vector_store": {"healthy": true, "status": "connected"},
    "task_queue": {"provider": "threaded", "status": "operational"},
    "notification_transport": {"provider": "sse", "status": "operational"}
  }
}
```

### Request Correlation Middleware

`RequestCorrelationMiddleware` (`backend/core/middleware.py`) is mounted on the FastAPI app and:

1. Reads or generates a unique `X-Request-ID` UUID per request.
2. Attaches it to `request.state` for downstream log correlation.
3. Measures wall-clock request duration.
4. Injects `X-Request-ID` and `X-Process-Time` response headers.
5. Emits a structured access-log line: `METHOD /path - STATUS (Xms) [req_id=...]`

This enables full end-to-end log tracing from browser to backend without modifying application business logic.

---

## 4. Secret-Safe Structured Logging

### SecretMaskingFilter

`SecretMaskingFilter` (`backend/core/logging.py`) is a Python `logging.Filter` attached to all log handlers at startup. It applies regex substitutions to every log message before it is written:

| Pattern | Replacement | Protects |
|---|---|---|
| `password=...` / `password: ...` | `***MASKED***` | Plaintext passwords |
| `access_token=...` | `***MASKED***` | OAuth access tokens |
| `Bearer <JWT>` | `Bearer ***MASKED_TOKEN***` | Raw JWT bearer tokens |
| `api_key=...` | `***MASKED***` | API keys |
| `secret=...` | `***MASKED***` | Generic secrets |

The filter is applied **at the `Handler` level**, so it protects all log output regardless of log level or which module emits the message.

### Log Format

```
YYYY-MM-DD HH:MM:SS [LEVEL] [CampusMind] <message>
```

Log level is controlled by `LOG_LEVEL` environment variable (default: `INFO`).

---

## 5. Production Configuration Fail-Closed

`Settings.validate_production_config()` (`backend/core/config.py`) enforces:

| Check | Fail Condition |
|---|---|
| `JWT_SECRET_KEY` | Absent, < 32 chars, or matches known weak defaults |
| `GEMINI_API_KEY` | Empty or placeholder value |
| `OIDC_METADATA_URL` | Empty in production |
| `DEMO_MODE` | Enabled in production |

Any of these raises `ValueError` at startup — the application process exits before accepting traffic, preventing insecure deployment.

---

## 6. Database Connection Reliability

`check_database_health()` (`backend/db/session.py`) executes `text('SELECT 1')` within an explicit transaction, correctly using the SQLAlchemy 2.0 `execute(text(...))` API. Pool configuration via environment:

| Setting | Default | Purpose |
|---|---|---|
| `DB_POOL_SIZE` | 5 | Base connection pool size |
| `DB_MAX_OVERFLOW` | 10 | Maximum overflow connections |
| `DB_POOL_TIMEOUT` | 30s | Wait timeout for connection |
| `DB_POOL_RECYCLE` | 1800s | Max connection age (prevents stale) |
| `DB_POOL_PRE_PING` | `true` | Validates connections before checkout |

`DB_POOL_PRE_PING=true` ensures broken database connections (e.g., after a PostgreSQL restart) are transparently recycled without 500 errors reaching users.

---

## 7. Frontend Real-Time Integration

`frontend/src/lib/api.js` exposes `subscribeToNotificationStream(token, onMessage, onError)` which:

1. Opens an `EventSource` to `/api/v1/notifications/stream?token=<jwt>`.
2. Listens for `notification` and `sse_connected` event types.
3. Calls `onMessage(data)` for each notification.
4. Falls back gracefully if `EventSource` is unsupported.

`Header.jsx` connects to this stream on mount (after login) and populates the notification badge and dropdown with real-time events, with proper cleanup on unmount.

---

## 8. Security Invariants Preserved

Phase 8 was implemented without weakening any Phase 0–7 security boundary:

| Invariant | Phase 8 Impact |
|---|---|
| JWT authentication on all protected endpoints | SSE stream authenticates via token before streaming |
| RBAC / role enforcement | No new privileged endpoints added without role checks |
| Student data isolation (IDOR protection) | Notification isolation is structurally enforced by `user_id` keyed queues |
| Secret masking in logs | Extended — `SecretMaskingFilter` applied globally at startup |
| Fail-closed on bad configuration | `validate_production_config()` exits on weak secrets |
| No credentials in task failure details | Sanitized error string `Task failed: <ExceptionType>` only |
| Health endpoints do not expose credentials | Dependency map contains status strings only |

---

## 9. Test Coverage

Phase 8 adds `tests/test_phase8_production.py` (13 test functions, all named per area):

| Test ID | Area Covered |
|---|---|
| A & B | Distributed task submission & state transitions |
| C | Failed task handling & sanitized error recording |
| D | Duplicate prevention / idempotency key behavior |
| E & F | Notification authorization & user isolation |
| G & H | SSE stream JWT authentication & content-type verification |
| I | Request correlation header injection (`X-Request-ID`, `X-Process-Time`) |
| J | `SecretMaskingFilter` password & bearer token masking |
| K | Liveness probe returns `status: alive` |
| L & M | Readiness probe & dependency health map structure |
| N | Production config fail-closed (`ValueError` on weak secret) |
| O | `check_database_health()` SQLAlchemy 2.0 compatibility |
| P | Phase 6 SSO/governance security regression |
| Q | Phase 7 intervention authorization regression |

---

## 10. Deployment Notes

### Docker / Kubernetes Health Probes

```yaml
livenessProbe:
  httpGet:
    path: /health/liveness
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 15

readinessProbe:
  httpGet:
    path: /health/readiness
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10
  failureThreshold: 3
```

### Required Environment Variables (Production)

```env
APP_ENV=production
JWT_SECRET_KEY=<min 32 chars, unique, random>
GEMINI_API_KEY=<real key>
OIDC_METADATA_URL=<your OIDC provider metadata endpoint>
DATABASE_URL=postgresql+psycopg2://user:pass@host/db
TASK_QUEUE_PROVIDER=threaded      # or redis for multi-instance
REDIS_URL=redis://redis:6379/0    # required if TASK_QUEUE_PROVIDER=redis
NOTIFICATION_TRANSPORT=sse
DB_POOL_PRE_PING=true
LOG_LEVEL=INFO
```

### Scaling Considerations

- **Single instance:** `TASK_QUEUE_PROVIDER=threaded` — tasks run in daemon threads within the API process.
- **Multi-instance horizontal scaling:** Switch `TASK_QUEUE_PROVIDER=redis` and provide `REDIS_URL`. The current implementation dispatches threads but the abstraction is designed to plug in Celery or ARQ workers without changes to calling code.
- **SSE notification scaling:** The current in-process `asyncio.Queue` registry works per-instance. For multi-instance deployments, replace `NotificationTransportManager` with a Redis Pub/Sub or NATS backend while preserving the same `subscribe` / `publish_notification` / `stream_user_events` interface.

---

## 11. File Change Summary (Phase 8)

| File | Change |
|---|---|
| `backend/models/schemas.py` | Added `LivenessCheckResponse`, `ReadinessCheckResponse`, `DependencyHealthResponse` |
| `backend/api/routes_system.py` | Added `/health/liveness`, `/health/readiness`, `/health/dependencies` endpoints |
| `backend/core/tasks.py` | Full `BackgroundTaskManager` with state machine, deduplication, retry, `get_task_status` |
| `backend/core/notifications.py` | `NotificationTransportManager`: subscribe/publish/stream SSE with user isolation |
| `backend/core/middleware.py` | `RequestCorrelationMiddleware`: `X-Request-ID`, `X-Process-Time` injection |
| `backend/core/logging.py` | `SecretMaskingFilter`: regex masking for passwords, tokens, API keys |
| `backend/db/session.py` | Fixed `check_database_health` for SQLAlchemy 2.0 (`text('SELECT 1')`) |
| `frontend/src/lib/api.js` | `subscribeToNotificationStream` SSE helper |
| `frontend/src/components/Header.jsx` | Connected to real-time notification stream |
| `tests/test_phase8_production.py` | 13-test Phase 8 production test suite |
