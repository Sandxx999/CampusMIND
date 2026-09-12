"""Tests for Phase 3 Campus Events Domain."""

import pytest
from fastapi.testclient import TestClient
from main import app
from auth.jwt_handler import create_access_token

client = TestClient(app)


def get_token(username: str, role: str) -> str:
    return create_access_token({"sub": username, "role": role})


def test_list_campus_events():
    token = get_token("student1", "student")
    response = client.get(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "events" in data


def test_admin_create_campus_event():
    token = get_token("admin1", "admin")
    payload = {
        "title": "Annual Campus Cultural Fest",
        "description": "Celebrating diversity and talent across departments.",
        "location": "Main Grounds",
        "start_time": "2026-10-01T10:00:00Z",
        "end_time": "2026-10-01T18:00:00Z",
        "category": "cultural"
    }
    response = client.post(
        "/api/v1/events",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Annual Campus Cultural Fest"


def test_user_register_for_event():
    token = get_token("student1", "student")
    response = client.post(
        "/api/v1/events/evt_001/register",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code in [200, 404]
