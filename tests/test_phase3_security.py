"""Phase 3 Comprehensive Privacy & Security Audit Tests.

Verifies strict server-side authorization enforcement, IDOR protection, role boundaries, and zero-leak privacy controls.
"""

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


def test_idor_attendance_access():
    """Student A (2024IFHE001) attempting to fetch Student B (2024IFHE002) attendance must fail with 403."""
    token_std1 = get_token("student1", "student", enrollment_no="2024IFHE001")
    resp = client.get(
        "/api/v1/attendance/student/2024IFHE002",
        headers={"Authorization": f"Bearer {token_std1}"}
    )
    assert resp.status_code == 403
    assert "Access denied" in resp.json()["detail"]


def test_idor_assessment_results_access():
    """Student A (2024IFHE001) attempting to fetch Student B (2024IFHE002) results must fail with 403."""
    token_std1 = get_token("student1", "student", enrollment_no="2024IFHE001")
    resp = client.get(
        "/api/v1/assessments/student/2024IFHE002",
        headers={"Authorization": f"Bearer {token_std1}"}
    )
    assert resp.status_code == 403
    assert "Access denied" in resp.json()["detail"]


def test_student_forbidden_from_modifying_attendance():
    """Students attempting to record attendance must be rejected with 403."""
    token_std1 = get_token("student1", "student", enrollment_no="2024IFHE001")
    resp = client.post(
        "/api/v1/attendance/offering/offering_cs301_fall24",
        json={"records": [{"enrollment_no": "2024IFHE001", "status": "present"}]},
        headers={"Authorization": f"Bearer {token_std1}"}
    )
    assert resp.status_code == 403


def test_student_forbidden_from_submitting_grades():
    """Students attempting to submit grades must be rejected with 403."""
    token_std1 = get_token("student1", "student", enrollment_no="2024IFHE001")
    resp = client.post(
        "/api/v1/assessments/asm_midterm_cs101/grades",
        json={"grades": [{"enrollment_no": "2024IFHE001", "obtained_marks": 100.0}]},
        headers={"Authorization": f"Bearer {token_std1}"}
    )
    assert resp.status_code == 403


def test_student_forbidden_from_publishing_announcements():
    """Students attempting to publish announcements must be rejected with 403."""
    token_std1 = get_token("student1", "student", enrollment_no="2024IFHE001")
    resp = client.post(
        "/api/v1/announcements",
        json={"title": "Hacked Announcement", "content": "Fake content"},
        headers={"Authorization": f"Bearer {token_std1}"}
    )
    assert resp.status_code == 403


def test_grade_out_of_bounds_rejection():
    """Submitting obtained_marks > max_marks must be rejected with 400 Bad Request."""
    token_faculty = get_token("faculty1", "faculty")

    # Create assessment with max_marks = 50
    asm_resp = client.post(
        "/api/v1/assessments",
        json={"title": "Quiz Test Bounds", "assessment_type": "quiz", "max_marks": 50.0},
        headers={"Authorization": f"Bearer {token_faculty}"}
    )
    asm_id = asm_resp.json()["id"]

    # Test obtained_marks > max_marks
    resp_over = client.post(
        f"/api/v1/assessments/{asm_id}/grades",
        json={"grades": [{"enrollment_no": "2024IFHE001", "obtained_marks": 999.0}]},
        headers={"Authorization": f"Bearer {token_faculty}"}
    )
    assert resp_over.status_code == 400
    assert "Invalid obtained marks" in resp_over.json()["detail"]

    # Test obtained_marks < 0
    resp_under = client.post(
        f"/api/v1/assessments/{asm_id}/grades",
        json={"grades": [{"enrollment_no": "2024IFHE001", "obtained_marks": -10.0}]},
        headers={"Authorization": f"Bearer {token_faculty}"}
    )
    assert resp_under.status_code == 400
