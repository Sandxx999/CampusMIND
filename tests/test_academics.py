"""Tests for Phase 3 Academic Domain (Terms and Course Offerings)."""

import pytest
from fastapi.testclient import TestClient
from main import app
from auth.jwt_handler import create_access_token

client = TestClient(app)


def get_token(username: str, role: str) -> str:
    return create_access_token({"sub": username, "role": role})


def test_get_current_term():
    token = get_token("student1", "student")
    response = client.get(
        "/api/v1/academics/terms/current",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "code" in data
    assert data["is_current"] is True


def test_list_terms():
    token = get_token("student1", "student")
    response = client.get(
        "/api/v1/academics/terms",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "terms" in data
    assert data["total"] >= 1


def test_student_cannot_create_term():
    token = get_token("student1", "student")
    payload = {
        "code": "2026-SPRING",
        "name": "Spring 2026",
        "academic_year": "2025-2026",
        "semester": 2
    }
    response = client.post(
        "/api/v1/academics/terms",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_admin_can_create_term():
    token = get_token("admin1", "admin")
    payload = {
        "code": "2026-SPRING-TEST",
        "name": "Spring 2026 Test",
        "academic_year": "2025-2026",
        "semester": 2
    }
    response = client.post(
        "/api/v1/academics/terms",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "2026-SPRING-TEST"


def test_list_course_offerings():
    token = get_token("student1", "student")
    response = client.get(
        "/api/v1/academics/offerings",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "offerings" in data
    assert data["total"] >= 1
