"""Tests for Phase 3 Knowledge Foundation Metadata Domain."""

import pytest
from fastapi.testclient import TestClient
from main import app
from auth.jwt_handler import create_access_token

client = TestClient(app)


def get_token(username: str, role: str) -> str:
    return create_access_token({"sub": username, "role": role})


def test_list_knowledge_documents():
    token = get_token("student1", "student")
    response = client.get(
        "/api/v1/knowledge",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data


def test_admin_create_knowledge_document():
    token = get_token("admin1", "admin")
    payload = {
        "title": "Examination Grading & Evaluation Policy",
        "file_path": "data/grading_policy.txt",
        "category": "policy",
        "version": "2025.1"
    }
    response = client.post(
        "/api/v1/knowledge",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Examination Grading & Evaluation Policy"
