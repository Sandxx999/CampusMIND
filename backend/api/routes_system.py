import os
from fastapi import APIRouter, HTTPException, status, Request
from core.config import settings
from db.session import check_database_health
from models.schemas import (
    HealthCheckResponse,
    LivenessCheckResponse,
    ReadinessCheckResponse,
    DependencyHealthResponse,
)

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthCheckResponse)
@router.get("/api/v1/health", response_model=HealthCheckResponse)
def health_check():
    """System health check endpoint returning overall operational status."""
    return HealthCheckResponse(
        status="healthy",
        service="CampusMind RAG Assistant",
        version="2.0.0",
        environment=settings.APP_ENV,
    )


@router.get("/health/liveness", response_model=LivenessCheckResponse)
@router.get("/liveness", response_model=LivenessCheckResponse)
@router.get("/api/v1/health/liveness", response_model=LivenessCheckResponse)
def liveness_check():
    """
    Liveness probe. Indicates if the application process is running.
    Does NOT check external dependencies (database, vector store, redis).
    """
    return LivenessCheckResponse(
        status="alive",
        service="CampusMind RAG Assistant",
        version="2.0.0",
        environment=settings.APP_ENV,
    )


@router.get("/ready", response_model=ReadinessCheckResponse)
@router.get("/health/readiness", response_model=ReadinessCheckResponse)
@router.get("/api/v1/ready", response_model=ReadinessCheckResponse)
@router.get("/api/v1/health/readiness", response_model=ReadinessCheckResponse)
def readiness_check(req: Request):
    """
    Readiness probe. Verifies database, vector store, and task queue readiness.
    Fails with 503 HTTP status if critical dependencies are not ready.
    """
    if not getattr(req.app.state, "is_ready", True):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System initialization in progress."
        )

    db_ok, db_msg = check_database_health()
    db_status = "connected" if db_ok else "unhealthy"

    chroma_status = "connected" if os.path.exists(settings.CHROMA_DB_DIR) else "not_initialized"

    task_provider = settings.TASK_QUEUE_PROVIDER
    task_queue_status = "operational"
    if task_provider == "redis":
        try:
            import redis
            r = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=2.0)
            if r.ping():
                task_queue_status = "connected"
            else:
                task_queue_status = "unresponsive"
        except Exception:
            task_queue_status = "unhealthy"

    if not db_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System database component is not ready.",
        )

    db_type = settings.DATABASE_URL.split("://")[0] if settings.DATABASE_URL else "unknown"

    return ReadinessCheckResponse(
        status="ready",
        database=db_status,
        chroma_db=chroma_status,
        task_queue=task_queue_status,
        details={
            "database_type": db_type,
            "task_queue_provider": task_provider,
        },
    )


@router.get("/health/dependencies", response_model=DependencyHealthResponse)
@router.get("/api/v1/health/dependencies", response_model=DependencyHealthResponse)
def dependency_health_check():
    """
    Detailed dependency health inspection endpoint.
    Exposes dependency statuses without leaking credentials or stack traces.
    """
    db_ok, db_msg = check_database_health()
    chroma_exists = os.path.exists(settings.CHROMA_DB_DIR)

    task_provider = settings.TASK_QUEUE_PROVIDER
    t_status = "operational"
    if task_provider == "redis":
        try:
            import redis
            r = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=2.0)
            t_status = "connected" if r.ping() else "unresponsive"
        except Exception:
            t_status = "unhealthy"

    overall_status = "healthy" if db_ok else "degraded"

    return DependencyHealthResponse(
        status=overall_status,
        dependencies={
            "database": {
                "healthy": db_ok,
                "status": "connected" if db_ok else "unhealthy",
            },
            "vector_store": {
                "healthy": chroma_exists,
                "status": "connected" if chroma_exists else "not_initialized",
            },
            "task_queue": {
                "provider": task_provider,
                "status": t_status,
            },
            "notification_transport": {
                "provider": settings.NOTIFICATION_TRANSPORT,
                "status": "operational",
            },
        },
    )

