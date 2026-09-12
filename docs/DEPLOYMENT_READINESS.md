# CampusMIND 2.0 — Production Deployment & Readiness (Phase 12)

## 1. Release Status

**CODE READY**: YES. The codebase has passed the strict Phase 0–12 production gate, full regression testing (210/210 passed), and all security invariants (IDOR, RBAC, JWT, RAG Privacy, Export Security).
**INFRASTRUCTURE READY**: PENDING. Deployment into production requires provisioning external dependencies (PostgreSQL, Redis) and explicit environment configurations.

## 2. Infrastructure Dependencies

For a true production deployment, the following external infrastructure is REQUIRED:

- **Database**: PostgreSQL 14+ (SQLite is supported but NOT recommended for multi-worker production).
- **In-Memory Store / PubSub**: Redis 6+ (Required for SSE cross-worker scaling and distributed `BackgroundTaskManager`).
- **Persistent Storage**: High-I/O volume for ChromaDB (`CHROMA_DB_DIR`) persistent indexing.
- **Compute**: Stateless containers (Docker/Kubernetes) capable of handling concurrent FastAPI workers.

## 3. Production Environment Configuration

The following environment variables MUST be explicitly set in the production environment. Do NOT use `.env` files in production; inject these via your secret manager or orchestration platform.

### Required Secrets
- `APP_ENV`: Must be exactly `production`.
- `JWT_SECRET_KEY`: Must be a cryptographically secure random string (>= 32 characters).
- `GEMINI_API_KEY`: A valid Google Gemini API key.
- `DATABASE_URL`: Full PostgreSQL connection string (e.g., `postgresql://user:password@host:port/dbname`).
- `REDIS_URL`: Full Redis connection string (e.g., `redis://:password@host:6379/0`).

### Required Configuration
- `CORS_ORIGINS`: Explicit comma-separated list of allowed frontend URLs (e.g., `https://campus.edu,https://admin.campus.edu`). Cannot contain `*`.
- `DEMO_MODE`: Must be `false`.
- `TASK_QUEUE_PROVIDER`: Should be `redis` for production scaling (falls back to `threaded` for single-node degraded mode).
- `NOTIFICATION_TRANSPORT`: Should be `redis` for multi-worker SSE scaling.
- `CHROMA_DB_DIR`: Absolute path to a mounted persistent volume.

## 4. Deployment Commands

### Application Startup (Backend)
```bash
# Run FastAPI with Gunicorn and Uvicorn workers
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Database Migration
Before starting the application workers, the database schema must be initialized:
```bash
alembic upgrade head
```

### Frontend Build & Deployment
```bash
# In the frontend/ directory
npm install
npm run build
# Deploy the contents of frontend/dist to a CDN or static web host (e.g., Nginx, S3, Vercel)
```

## 5. Security Model & Best Practices

- **Health Probes**: Liveness (`/api/v1/system/liveness`) and Readiness (`/api/v1/system/readiness`) endpoints are safe for public uptime monitors and load balancers. They do not leak internal credentials or stack traces.
- **Rollback Considerations**: Application rollbacks require checking Alembic down-revisions. Only downgrade the database if the schema changes introduced backward incompatibilities.
- **Scaling Limitations**: The `threaded` background task provider will NOT scale across multiple pods. You MUST configure `REDIS_URL` and set `TASK_QUEUE_PROVIDER=redis` to ensure SSE and background events propagate correctly in a multi-node cluster.
- **Monitoring Requirements**: Monitor worker memory consumption, ChromaDB I/O latency, and Redis pub/sub queue lengths. All API endpoints emit structured JSON logs suitable for Datadog, ELK, or CloudWatch.
