"""Tests for Phase 3 Unified Institutional Search."""

import pytest
from fastapi.testclient import TestClient
from main import app
from auth.jwt_handler import create_access_token

client = TestClient(app)


def get_token(username: str, role: str) -> str:
    return create_access_token({"sub": username, "role": role})


def test_unified_search():
    token = get_token("student1", "student")
    response = client.get(
        "/api/v1/search?q=Campus",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "Campus"
    assert "courses" in data
    assert "announcements" in data
    assert "events" in data
    assert "documents" in data
