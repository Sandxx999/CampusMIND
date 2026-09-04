import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
from main import app

client = TestClient(app)

def get_auth_headers():
    login_res = client.post("/api/auth/login", json={
        "username": "student1",
        "password": "password123",
        "role": "student"
    })
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_list_students():
    headers = get_auth_headers()
    response = client.get("/api/students", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 100
    assert len(data["students"]) == 50 # Default limit
    first_student = data["students"][0]
    assert first_student["enrollment_no"] == "2024IFHE001"
    assert "mobile_no" in first_student
    assert "courses_enrolled" in first_student
    assert "cgpa" in first_student

def test_get_single_student():
    headers = get_auth_headers()
    response = client.get("/api/students/2024IFHE042", headers=headers)
    assert response.status_code == 200
    student = response.json()
    assert student["enrollment_no"] == "2024IFHE042"
    assert student["mobile_no"].startswith("+91")
    assert student["cgpa"] > 0

def test_student_stats_summary():
    headers = get_auth_headers()
    response = client.get("/api/students/stats/summary", headers=headers)
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_students"] == 100
    assert stats["avg_cgpa"] > 0
    assert "Computer Science & Engineering (CSE)" in stats["branch_distribution"]

def test_rag_query_student_details():
    headers = get_auth_headers()
    res = client.post("/api/chat", json={
        "message": "Find details and courses enrolled for student 2024IFHE001"
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "2024IFHE001" in data["answer"]
