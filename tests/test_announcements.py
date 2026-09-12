"""Tests for Phase 3 Institutional Announcements Domain."""

import pytest
from fastapi.testclient import TestClient
from main import app
from auth.jwt_handler import create_access_token

client = TestClient(app)


def get_token(username: str, role: str) -> str:
    return create_access_token({"sub": username, "role": role})


def test_list_announcements():
    token = get_token("student1", "student")
    response = client.get(
        "/api/v1/announcements",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "announcements" in data
    assert data["total"] >= 1


def test_student_cannot_create_announcement():
    token = get_token("student1", "student")
    payload = {
        "title": "Fake Announcement by Student",
        "content": "This should be blocked."
    }
    response = client.post(
        "/api/v1/announcements",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_faculty_can_create_announcement():
    token = get_token("faculty1", "faculty")
    payload = {
        "title": "Faculty Assignment Guidance",
        "content": "Please review the new guidelines for project submissions.",
        "audience": "students",
        "priority": "high"
    }
    response = client.post(
        "/api/v1/announcements",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Faculty Assignment Guidance"
    assert data["audience"] == "students"
