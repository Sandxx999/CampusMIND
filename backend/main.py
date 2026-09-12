import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from api.routes_auth import router as auth_router
from api.routes_chat import router as chat_router
from api.routes_admin import router as admin_router
from api.routes_students import router as students_router
from logs.logger import logger

app = FastAPI(
    title="CampusMind Enterprise RAG API",
    description="Backend API for Retrieval-Augmented Generation Campus Assistant with RBAC and citation tracking.",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(students_router)


import threading

@app.on_event("startup")
def startup_event():
    logger.info("Initializing CampusMind RAG system (background ingestion enabled)...")
    try:
        def run_ingestion():
            from rag.ingest import ingest_campus_data

            ingest_campus_data()

        thread = threading.Thread(target=run_ingestion, daemon=True)
        thread.start()
    except Exception as e:
        logger.error(f"Error starting background ingestion: {e}")

@app.get("/", tags=["Root"])
def root():
    """Welcome endpoint pointing to docs and healthcheck."""
    return {
        "message": "Welcome to CampusMind Enterprise RAG API",
        "health": "/health",
        "documentation": "/docs"
    }

@app.get("/health", tags=["Health"])
def health_check():
    """System health check endpoint returning API operational status."""
    return {
        "status": "healthy",
        "service": "CampusMind RAG Assistant",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    logger.info("Starting CampusMind FastAPI server on http://0.0.0.0:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
