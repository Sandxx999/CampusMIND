"""Tests for Phase 3 Assessment & Performance Domain."""

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


def test_faculty_create_assessment():
    token = get_token("faculty1", "faculty")
    payload = {
        "title": "Quiz 2: Data Structures",
        "assessment_type": "quiz",
        "max_marks": 25.0,
        "weightage": 10.0
    }
    response = client.post(
        "/api/v1/assessments",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Quiz 2: Data Structures"
    assert data["max_marks"] == 25.0


def test_student_cannot_create_assessment():
    token = get_token("student1", "student", enrollment_no="2024IFHE001")
    payload = {
        "title": "Unauthorized Assessment",
        "assessment_type": "quiz",
        "max_marks": 100.0
    }
    response = client.post(
        "/api/v1/assessments",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_record_grades_validation_bounds():
    token = get_token("faculty1", "faculty")
    create_resp = client.post(
        "/api/v1/assessments",
        json={"title": "Lab Test 1", "assessment_type": "lab", "max_marks": 50.0},
        headers={"Authorization": f"Bearer {token}"}
    )
    asm_id = create_resp.json()["id"]

    # Attempt obtained_marks > max_marks (60 > 50) -> should fail with 400
    invalid_payload = {
        "grades": [
            {"enrollment_no": "2024IFHE001", "obtained_marks": 60.0}
        ]
    }
    resp_invalid = client.post(
        f"/api/v1/assessments/{asm_id}/grades",
        json=invalid_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp_invalid.status_code == 400

    # Submit valid marks -> 45/50
    valid_payload = {
        "grades": [
            {"enrollment_no": "2024IFHE001", "obtained_marks": 45.0, "grade": "A"}
        ]
    }
    resp_valid = client.post(
        f"/api/v1/assessments/{asm_id}/grades",
        json=valid_payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp_valid.status_code == 200
    assert resp_valid.json()["recorded_count"] == 1


def test_student_get_own_results():
    token = get_token("student1", "student", enrollment_no="2024IFHE001")
    response = client.get(
        "/api/v1/assessments/student/2024IFHE001",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["enrollment_no"] == "2024IFHE001"
    assert "results" in data


def test_student_cannot_get_other_results():
    token = get_token("student1", "student", enrollment_no="2024IFHE001")
    response = client.get(
        "/api/v1/assessments/student/2024IFHE002",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
