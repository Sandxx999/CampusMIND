"""Phase 7 Intelligent Interventions, Action Plans & Notifications Test Suite.

Verifies creation, RBAC, IDOR protection, notification dispatch, and action plan tracking.
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from auth.jwt_handler import create_access_token
from db.session import get_db_session
from db.models import StudentProfile, User

client = TestClient(app)


def get_token(username: str, role: str, enrollment_no: str = None) -> str:
    token_data = {"sub": username, "role": role, "enrollment_no": enrollment_no}
    return create_access_token(token_data)


def test_create_intervention_faculty():
    """Verifies that faculty can issue an academic intervention notice for a student."""
    with get_db_session() as session:
        student = session.query(StudentProfile).first()
        assert student is not None, "Student profile must exist in test database"
        student_profile_id = student.id

    token = get_token("faculty1", "faculty")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "student_profile_id": student_profile_id,
        "risk_category": "attendance",
        "title": "Low Attendance Warning",
        "description": "Student attendance has dropped below 70% requirement.",
        "recommended_action": "Attend next 4 consecutive classes without absence.",
    }

    response = client.post("/api/v1/interventions", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["student_profile_id"] == student_profile_id
    assert data["risk_category"] == "attendance"
    assert data["status"] == "pending"


def test_create_intervention_student_blocked():
    """Verifies that students CANNOT issue academic interventions."""
    token = get_token("student1", "student", "2024-CSE-001")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "student_profile_id": "some_id",
        "risk_category": "attendance",
        "title": "Test Title",
        "description": "Test Desc",
        "recommended_action": "Test Action",
    }

    response = client.post("/api/v1/interventions", json=payload, headers=headers)
    assert response.status_code == 403


def test_list_interventions_student_idor():
    """Verifies that students can only see their own interventions."""
    token = get_token("student1", "student", "2024IFHE001")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/interventions", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "interventions" in data
    for item in data["interventions"]:
        assert item["enrollment_no"] == "2024IFHE001"


def test_student_acknowledge_intervention():
    """Verifies that student can acknowledge an intervention notice."""
    token_faculty = get_token("faculty1", "faculty")
    headers_faculty = {"Authorization": f"Bearer {token_faculty}"}

    with get_db_session() as session:
        student = session.query(StudentProfile).filter(StudentProfile.enrollment_no == "2024IFHE001").first()
        student_profile_id = student.id

    create_resp = client.post(
        "/api/v1/interventions",
        json={
            "student_profile_id": student_profile_id,
            "risk_category": "performance",
            "title": "Assessment Advisory",
            "description": "Midterm score below threshold.",
            "recommended_action": "Schedule office hours consultation.",
        },
        headers=headers_faculty,
    )
    assert create_resp.status_code == 200
    intervention_id = create_resp.json()["id"]

    token_student = get_token("student1", "student", "2024IFHE001")
    headers_student = {"Authorization": f"Bearer {token_student}"}

    update_resp = client.patch(
        f"/api/v1/interventions/{intervention_id}",
        json={"status": "acknowledged", "resolution_notes": "I will attend office hours next Monday."},
        headers=headers_student,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "acknowledged"


def test_create_and_list_action_plans():
    """Verifies creation and listing of student recovery action plans."""
    token = get_token("student1", "student", "2024IFHE001")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "title": "Semester 4 Recovery Plan",
        "target_attendance_pct": 78.5,
        "target_sgpa": 8.0,
        "milestones": [
            "Complete all lab assignments on time",
            "Attend 100% of morning lecture sessions",
        ],
    }

    create_resp = client.post("/api/v1/plans", json=payload, headers=headers)
    assert create_resp.status_code == 200
    plan_data = create_resp.json()
    assert plan_data["title"] == "Semester 4 Recovery Plan"
    assert len(plan_data["milestones"]) == 2

    list_resp = client.get("/api/v1/plans", headers=headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1


def test_user_notifications():
    """Verifies listing and marking user notifications as read."""
    token = get_token("student1", "student", "2024IFHE001")
    headers = {"Authorization": f"Bearer {token}"}

    list_resp = client.get("/api/v1/notifications", headers=headers)
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert "unread_count" in data
    assert "notifications" in data

    if data["notifications"]:
        notif_ids = [n["id"] for n in data["notifications"]]
        mark_resp = client.post("/api/v1/notifications/mark-read", json={"notification_ids": notif_ids}, headers=headers)
        assert mark_resp.status_code == 200
        assert mark_resp.json()["updated"] >= 1
