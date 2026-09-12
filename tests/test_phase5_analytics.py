"""
Phase 5 Academic Analytics Test Suite for CampusMIND 2.0.

Validates attendance risk analysis, recovery calculations, performance analytics,
recommendation generation, query intent routing, security & authorization boundaries,
audit logging, and API response schemas.
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from analytics.risk_engine import attendance_risk_engine
from analytics.recommendation_engine import recommendation_engine
from analytics.query_router import academic_query_router
from analytics.engine import analytics_engine
from auth.jwt_handler import create_access_token
from db.session import get_db_session

from db.models import User, Role, StudentProfile, FacultyProfile, CourseOffering, AttendanceRecord, Assessment, AssessmentGrade


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def student_auth_headers():
    token = create_access_token(data={"sub": "student1", "role": "student", "enrollment_no": "2024IFHE001"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def student2_auth_headers():
    token = create_access_token(data={"sub": "student2", "role": "student", "enrollment_no": "2024IFHE002"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def faculty_auth_headers():
    token = create_access_token(data={"sub": "faculty1", "role": "faculty"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers():
    token = create_access_token(data={"sub": "admin1", "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


# -----------------------------------------------------------------------------
# 1. ATTENDANCE RISK & RECOVERY CALCULATIONS
# -----------------------------------------------------------------------------

def test_attendance_risk_safe():
    res = attendance_risk_engine.calculate_risk(attended_classes=8, conducted_classes=10, required_pct=75.0)
    assert res["risk_level"] == "SAFE"
    assert res["attendance_percentage"] == 80.0
    assert res["deficit_percentage"] == 0.0
    assert res["classes_needed_to_recover"] == 0
    assert res["is_recoverable"] is True
    assert "meets or exceeds" in res["explanation"]


def test_attendance_risk_watch():
    res = attendance_risk_engine.calculate_risk(attended_classes=7, conducted_classes=10, required_pct=75.0)
    assert res["risk_level"] == "WATCH"
    assert res["attendance_percentage"] == 70.0
    assert res["deficit_percentage"] == 5.0
    assert res["classes_needed_to_recover"] == 2
    assert "below the required threshold" in res["explanation"]



def test_attendance_risk_at_risk():
    res = attendance_risk_engine.calculate_risk(attended_classes=6, conducted_classes=10, required_pct=75.0)
    assert res["risk_level"] == "AT_RISK"
    assert res["attendance_percentage"] == 60.0
    assert res["deficit_percentage"] == 15.0
    # Recovery check: (0.75*10 - 6) / 0.25 = 1.5 / 0.25 = 6 classes needed
    assert res["classes_needed_to_recover"] == 6
    assert "at risk below" in res["explanation"]


def test_attendance_risk_critical():
    res = attendance_risk_engine.calculate_risk(attended_classes=5, conducted_classes=10, required_pct=75.0)
    assert res["risk_level"] == "CRITICAL"
    assert res["attendance_percentage"] == 50.0
    assert res["deficit_percentage"] == 25.0
    # Recovery check: (0.75*10 - 5) / 0.25 = 2.5 / 0.25 = 10 classes needed
    assert res["classes_needed_to_recover"] == 10
    assert "critically low" in res["explanation"]


def test_attendance_risk_insufficient_data():
    res = attendance_risk_engine.calculate_risk(attended_classes=0, conducted_classes=0, required_pct=75.0)
    assert res["risk_level"] == "UNKNOWN"
    assert res["insufficient_data"] is True
    assert "Insufficient" in res["explanation"]


# -----------------------------------------------------------------------------
# 2. RECOMMENDATION ENGINE TESTS
# -----------------------------------------------------------------------------

def test_recommendation_engine_critical_risk():
    risk = {
        "risk_level": "CRITICAL",
        "attendance_percentage": 50.0,
        "required_percentage": 75.0,
        "classes_needed_to_recover": 10,
        "insufficient_data": False,
    }
    perf = {"assessment_average": 45.0, "total_assessments": 3, "weakest_subjects": []}
    profile = {"cgpa": 7.2, "backlogs": 1}

    recs = recommendation_engine.generate_student_recommendations(risk, perf, profile)
    assert len(recs) >= 3

    severities = [r["severity"] for r in recs]
    assert "critical" in severities
    sources = [r["source"] for r in recs]
    assert "attendance_records" in sources
    assert "assessment_grades" in sources
    assert "student_profile" in sources


def test_recommendation_engine_strong_performance():
    risk = {
        "risk_level": "SAFE",
        "attendance_percentage": 90.0,
        "required_percentage": 75.0,
        "classes_needed_to_recover": 0,
        "insufficient_data": False,
    }
    perf = {"assessment_average": 85.0, "total_assessments": 4, "weakest_subjects": []}
    profile = {"cgpa": 8.8, "backlogs": 0}

    recs = recommendation_engine.generate_student_recommendations(risk, perf, profile)
    severities = [r["severity"] for r in recs]
    assert "positive" in severities


# -----------------------------------------------------------------------------
# 3. QUERY INTENT ROUTING TESTS
# -----------------------------------------------------------------------------

def test_query_routing_intents():
    r1 = academic_query_router.classify_academic_query("What is my attendance?")
    assert r1["intent"] == "STUDENT_ACADEMIC_DATA"

    r2 = academic_query_router.classify_academic_query("Am I at risk in attendance?")
    assert r2["intent"] == "STUDENT_ANALYTICS"

    r3 = academic_query_router.classify_academic_query("What attendance do I need to maintain?")
    assert r3["intent"] == "STUDENT_ANALYTICS"
    assert r3["combined_policy_personal"] is True

    r4 = academic_query_router.classify_academic_query("What is the attendance policy?")
    assert r4["intent"] == "INSTITUTIONAL_KNOWLEDGE"

    r5 = academic_query_router.classify_academic_query("Show attendance statistics for the CSE department")
    assert r5["intent"] == "ADMIN_ANALYTICS"


# -----------------------------------------------------------------------------
# 4. API ENDPOINTS & AUTHORIZATION BOUNDARY TESTS
# -----------------------------------------------------------------------------

def test_student_me_analytics_endpoint(client, student_auth_headers):
    response = client.get("/api/v1/analytics/student/me", headers=student_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "student_profile" in data
    assert "attendance_summary" in data
    assert "performance_summary" in data
    assert "risk_analysis" in data
    assert "recommendations" in data


def test_student_me_attendance_endpoint(client, student_auth_headers):
    response = client.get("/api/v1/analytics/student/me/attendance", headers=student_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "overall_attendance_pct" in data
    assert "risk_analysis" in data


def test_student_me_performance_endpoint(client, student_auth_headers):
    response = client.get("/api/v1/analytics/student/me/performance", headers=student_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "cgpa" in data
    assert "sgpa" in data


def test_student_cannot_access_admin_analytics(client, student_auth_headers):
    response = client.get("/api/v1/analytics/admin/overview", headers=student_auth_headers)
    assert response.status_code == 403
    detail = response.json()["detail"]
    # Phase 9 defense-in-depth: router-level require_role fires first (preferred message),
    # or service-layer _enforce_admin_authorization message (also acceptable).
    assert (
        "System Admin authorization required" in detail
        or "not authorized for this resource" in detail
        or "Access denied" in detail
    ), f"Expected a 403 authorization detail, got: {detail}"



def test_admin_overview_analytics_endpoint(client, admin_auth_headers):
    response = client.get("/api/v1/analytics/admin/overview", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_students" in data
    assert "average_attendance_pct" in data


def test_faculty_offering_analytics_authorization(client, faculty_auth_headers, student_auth_headers):
    # Student calling faculty offering endpoint gets 403
    response = client.get("/api/v1/analytics/faculty/offerings/nonexistent_offering", headers=student_auth_headers)
    assert response.status_code == 403

    # Faculty calling offering endpoint with invalid offering ID gets 403 or 404
    response_f = client.get("/api/v1/analytics/faculty/offerings/invalid_offering", headers=faculty_auth_headers)
    assert response_f.status_code in (403, 404)


def test_client_supplied_role_forgery_fails(client):
    # Attempting to forge admin role in unauthenticated request fails with 401
    response = client.get("/api/v1/analytics/admin/overview", headers={"Role": "admin"})
    assert response.status_code == 401


# -----------------------------------------------------------------------------
# 5. CHAT ANALYTICS INTEGRATION TEST
# -----------------------------------------------------------------------------

def test_chat_query_academic_analytics_integration(client, student_auth_headers):
    response = client.post(
        "/api/v1/chat",
        json={"message": "What is my attendance?"},
        headers=student_auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "Attendance" in data["answer"] or "Calculated Personal Academic Metrics" in data["answer"]
