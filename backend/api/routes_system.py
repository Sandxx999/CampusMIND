import os
from fastapi import APIRouter, HTTPException, status
from core.config import settings
from db.session import get_db_connection
from models.schemas import HealthCheckResponse, ReadinessCheckResponse

router = APIRouter(tags=["System"])


@router.get("/health", response_model=HealthCheckResponse)
@router.get("/api/v1/health", response_model=HealthCheckResponse)
def health_check():
    """System health check endpoint returning operational status."""
    return HealthCheckResponse(
        status="healthy",
        service="CampusMind RAG Assistant",
        version="2.0.0",
        environment=settings.APP_ENV,
    )


@router.get("/ready", response_model=ReadinessCheckResponse)
@router.get("/api/v1/ready", response_model=ReadinessCheckResponse)
def readiness_check():
    """System readiness check verifying database and vector store connectivity."""
    db_status = "unknown"
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"unhealthy: {e}"

    chroma_status = "connected" if os.path.exists(settings.CHROMA_DB_DIR) else "not_initialized"

    if db_status != "connected":
        raise HTTPException(
            status_code=status.HTTP_530_SITE_IS_FROZEN_OR_DOWN
            if hasattr(status, "HTTP_530_SITE_IS_FROZEN_OR_DOWN")
            else 503,
            detail="System database component is not ready.",
        )

    return ReadinessCheckResponse(
        status="ready",
        database=db_status,
        chroma_db=chroma_status,
        details={
            "database_url": settings.DATABASE_URL.split("://")[0] + "://...",
            "chroma_dir": settings.CHROMA_DB_DIR,
        },
    )
