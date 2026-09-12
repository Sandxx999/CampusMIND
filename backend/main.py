import os
import sys
import threading
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from core.logging import logger
from core.middleware import RequestCorrelationMiddleware
from api.routes_auth import router as auth_router, router_v1 as auth_router_v1
from api.routes_chat import router as chat_router, router_v1 as chat_router_v1
from api.routes_admin import router as admin_router, router_v1 as admin_router_v1
from api.routes_students import router as students_router, router_v1 as students_router_v1
from api.routes_system import router as system_router
from api.routes_academics import router_v1 as academics_router_v1
from api.routes_attendance import router_v1 as attendance_router_v1
from api.routes_assessments import router_v1 as assessments_router_v1
from api.routes_announcements import router_v1 as announcements_router_v1
from api.routes_events import router_v1 as events_router_v1
from api.routes_knowledge import router_v1 as knowledge_router_v1
from api.routes_search import router_v1 as search_router_v1
from api.routes_analytics import router_v1 as analytics_router_v1




@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for application startup and shutdown tasks."""
    logger.info("Initializing CampusMind 2.0 RAG system foundation...")
    try:
        def run_ingestion():
            from rag.ingest import ingest_campus_data
            ingest_campus_data()

        thread = threading.Thread(target=run_ingestion, daemon=True)
        thread.start()
    except Exception as e:
        logger.error(f"Error starting background document ingestion worker: {e}")
    
    yield
    logger.info("Shutting down CampusMind 2.0 API server cleanly...")


app = FastAPI(
    title="CampusMIND 2.0 Intelligence Platform API",
    description="Modular Enterprise RAG Campus Assistant with RBAC, structured logging, repository abstractions, and citation tracking.",
    version="2.0.0",
    lifespan=lifespan,
)

# Custom Exception Handlers for consistent API error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "request_id": request_id,
            },
        },
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None)
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error occurred.",
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred on the server.",
                "request_id": request_id,
            },
        },
    )


# Middlewares
app.add_middleware(RequestCorrelationMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register System & Core Routers
app.include_router(system_router)

# Versioned API v1 Routers
app.include_router(auth_router_v1)
app.include_router(chat_router_v1)
app.include_router(admin_router_v1)
app.include_router(students_router_v1)
app.include_router(academics_router_v1)
app.include_router(attendance_router_v1)
app.include_router(assessments_router_v1)
app.include_router(announcements_router_v1)
app.include_router(events_router_v1)
app.include_router(knowledge_router_v1)
app.include_router(search_router_v1)
app.include_router(analytics_router_v1)


# Unversioned API Routers (for Phase 0 client compatibility)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(students_router)


@app.get("/", tags=["Root"])
def root():
    """Welcome endpoint pointing to API documentation and health check."""
    return {
        "message": "Welcome to CampusMIND 2.0 Enterprise API",
        "health": "/health",
        "readiness": "/ready",
        "documentation": "/docs",
        "version": "2.0.0",
    }


if __name__ == "__main__":
    logger.info("Starting CampusMIND FastAPI server on http://0.0.0.0:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
