import os
import sys
import uuid

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from config import Settings, parse_cors_origins, settings
from logs.logger import log_query_to_db
from main import app


# Security route tests must not launch the expensive background ingestion worker.
app.router.on_startup.clear()
client = TestClient(app)


def login_headers(username: str):
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "password123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_login_rejects_client_selected_role_and_unknown_demo_users():
    role_attempt = client.post(
        "/api/auth/login",
        json={"username": "student1", "password": "password123", "role": "admin"},
    )
    assert role_attempt.status_code == 422

    valid_login = client.post(
        "/api/auth/login",
        json={"username": "student1", "password": "password123"},
    )
    assert valid_login.status_code == 200
    assert valid_login.json()["user"]["role"] == "student"

    unknown_user = client.post(
        "/api/auth/login",
        json={"username": "attacker", "password": "password123"},
    )
    assert unknown_user.status_code == 401


def test_invalid_and_missing_authentication_are_rejected():
    missing_auth = client.get("/api/students")
    assert missing_auth.status_code == 401

    invalid_auth = client.get(
        "/api/students",
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert invalid_auth.status_code == 401


def test_student_cannot_access_another_students_record_or_aggregate_stats():
    student_headers = login_headers("student1")

    own_record = client.get("/api/students/2024IFHE001", headers=student_headers)
    assert own_record.status_code == 200

    other_record = client.get("/api/students/2024IFHE042", headers=student_headers)
    assert other_record.status_code == 403

    stats = client.get("/api/students/stats/summary", headers=student_headers)
    assert stats.status_code == 403


def test_feedback_requires_ownership_of_the_referenced_query():
    owner_query_id = f"security_owner_{uuid.uuid4().hex}"
    own_query_id = f"security_self_{uuid.uuid4().hex}"
    log_query_to_db(owner_query_id, "admin1", "admin", "test", "test", 1.0, 1, 1.0, False)
    log_query_to_db(own_query_id, "student1", "student", "test", "test", 1.0, 1, 1.0, False)

    student_headers = login_headers("student1")
    forbidden = client.post(
        "/api/chat/feedback",
        json={"query_id": owner_query_id, "is_positive": True},
        headers=student_headers,
    )
    assert forbidden.status_code == 403

    accepted = client.post(
        "/api/chat/feedback",
        json={"query_id": own_query_id, "is_positive": True},
        headers=student_headers,
    )
    assert accepted.status_code == 200


def test_cors_uses_explicit_configured_origins():
    allowed_origin = settings.CORS_ORIGINS[0]
    allowed = client.options(
        "/health",
        headers={
            "Origin": allowed_origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert allowed.headers["access-control-allow-origin"] == allowed_origin

    disallowed = client.options(
        "/health",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in disallowed.headers
    assert "*" not in settings.CORS_ORIGINS


def test_production_settings_fail_closed_for_missing_or_known_secrets(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("CORS_ORIGINS", "https://campusmind.example")
    monkeypatch.setenv("GEMINI_API_KEY", "configured-test-key")
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
        Settings()

    monkeypatch.setenv("JWT_SECRET_KEY", "campusmind_super_secret_jwt_key_2026")
    with pytest.raises(ValueError, match="Production JWT_SECRET_KEY"):
        Settings()


def test_cors_parser_rejects_wildcards():
    with pytest.raises(ValueError, match="must not contain"):
        parse_cors_origins("https://campusmind.example, *")
