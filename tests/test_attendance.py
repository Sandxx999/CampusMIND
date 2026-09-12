"""Tests for Phase 3 Attendance Domain."""

import pytest
from fastapi.testclient import TestClient
from main import app
from auth.jwt_handler import create_access_token

client = TestClient(app)


def get_token(username: str, role: str, enrollment_no: str = None) -> str:
    payload = {"sub": username, "role": role}
    if enrollment_no:
        payload["enrollment_no"] = enrollment_no
    return create_access_token(payload)


def test_student_get_own_attendance():
    token = get_token("student1", "student", enrollment_no="2024IFHE001")
    response = client.get(
        "/api/v1/attendance/student/2024IFHE001",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["enrollment_no"] == "2024IFHE001"
    assert "summary" in data
    assert "records" in data


def test_student_cannot_get_other_student_attendance():
    token = get_token("student1", "student", enrollment_no="2024IFHE001")
    response = client.get(
        "/api/v1/attendance/student/2024IFHE002",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_faculty_can_get_any_student_attendance():
    token = get_token("faculty1", "faculty")
    response = client.get(
        "/api/v1/attendance/student/2024IFHE001",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["enrollment_no"] == "2024IFHE001"


def test_student_cannot_record_attendance():
    token = get_token("student1", "student", enrollment_no="2024IFHE001")
    payload = {
        "records": [
            {"enrollment_no": "2024IFHE001", "status": "present"}
        ]
    }
    response = client.post(
        "/api/v1/attendance/offering/offering_cs301_fall24",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_faculty_can_record_attendance():
    token = get_token("faculty1", "faculty")
    payload = {
        "records": [
            {"enrollment_no": "2024IFHE001", "status": "present", "remarks": "On time"}
        ]
    }
    response = client.post(
        "/api/v1/attendance/offering/offering_cs301_fall24",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["recorded_count"] == 1
