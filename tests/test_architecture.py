import pytest
from fastapi.testclient import TestClient
import sys
import os
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from main import app
from core.config import Settings, parse_cors_origins, settings
from core.logging import SecretMaskingFilter, setup_logger
from db.session import get_db_connection
from repositories.student_repository import student_repository
from repositories.audit_repository import audit_repository
from services.student_service import student_service
from services.auth_service import auth_service

app.router.on_startup.clear()
client = TestClient(app)


def test_system_health_and_readiness_endpoints():
    """Verify /health and /ready endpoints on both root and /api/v1 paths."""
    for path in ["/health", "/api/v1/health"]:
        res = client.get(path)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["service"] == "CampusMind RAG Assistant"
        assert data["version"] == "2.0.0"

    for path in ["/ready", "/api/v1/ready"]:
        res = client.get(path)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ready"
        assert data["database"] == "connected"


def test_request_correlation_middleware_headers():
    """Verify X-Request-ID and X-Process-Time headers are present in response."""
    res = client.get("/health")
    assert res.status_code == 200
    assert "X-Request-ID" in res.headers
    assert res.headers["X-Request-ID"].startswith("req_")
    assert "X-Process-Time" in res.headers


def test_secret_masking_log_filter():
    """Verify SecretMaskingFilter masks sensitive tokens and passwords in log records."""
    masking_filter = SecretMaskingFilter()
    
    rec_pass = logging.LogRecord("test", logging.INFO, "", 0, "Login attempt password='secretpassword123'", (), None)
    masking_filter.filter(rec_pass)
    assert "secretpassword123" not in rec_pass.msg
    assert "***MASKED***" in rec_pass.msg

    rec_jwt = logging.LogRecord("test", logging.INFO, "", 0, "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c", (), None)
    masking_filter.filter(rec_jwt)
    assert "eyJhbGciOiJIUzI" not in rec_jwt.msg
    assert "***MASKED_TOKEN***" in rec_jwt.msg


def test_repositories_and_service_layer():
    """Verify StudentRepository and StudentService data access abstractions."""
    row = student_repository.get_by_enrollment("2024IFHE001")
    assert row is not None
    assert row["enrollment_no"] == "2024IFHE001"
    assert row["name"] == "Aarav Rao"

    stats = student_repository.get_stats_summary()
    assert stats["total_students"] == 100
    assert stats["avg_cgpa"] > 0

    total, students = student_repository.list_students(branch="CSE", limit=10)
    assert total > 0
    assert len(students) <= 10


def test_api_v1_versioned_auth_and_students():
    """Verify API v1 routes function identically to unversioned routes."""
    login_res = client.post("/api/v1/auth/login", json={"username": "student1", "password": "password123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    students_res = client.get("/api/v1/students", headers=headers)
    assert students_res.status_code == 200
    assert students_res.json()["total"] == 1
