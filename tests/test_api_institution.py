import pytest
from fastapi.testclient import TestClient
from main import app
from auth.jwt_handler import create_access_token

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def student_auth_headers():
    token = create_access_token(data={"sub": "student1", "role": "student", "enrollment_no": "2024IFHE001"})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def faculty_auth_headers():
    token = create_access_token(data={"sub": "faculty1", "role": "faculty"})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_auth_headers():
    token = create_access_token(data={"sub": "admin1", "role": "admin"})
    return {"Authorization": f"Bearer {token}"}

def test_admin_can_access_institution_overview(client: TestClient, admin_auth_headers: dict):
    response = client.get("/api/v1/institution/overview", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_students" in data
    assert "average_cgpa" in data
    assert "average_attendance_pct" in data

def test_student_cannot_access_institution_overview(client: TestClient, student_auth_headers: dict):
    response = client.get("/api/v1/institution/overview", headers=student_auth_headers)
    assert response.status_code == 403

def test_faculty_cannot_access_institution_overview(client: TestClient, faculty_auth_headers: dict):
    response = client.get("/api/v1/institution/overview", headers=faculty_auth_headers)
    assert response.status_code == 403

def test_admin_can_access_attendance_trends(client: TestClient, admin_auth_headers: dict):
    response = client.get("/api/v1/institution/attendance-trends", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_admin_can_access_performance_trends(client: TestClient, admin_auth_headers: dict):
    response = client.get("/api/v1/institution/performance-trends", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_admin_can_access_risk_summary(client: TestClient, admin_auth_headers: dict):
    response = client.get("/api/v1/institution/risk-summary", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_students" in data
    assert "at_risk_count" in data

def test_admin_can_access_interventions_summary(client: TestClient, admin_auth_headers: dict):
    response = client.get("/api/v1/institution/interventions-summary", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_interventions" in data

def test_admin_can_access_department_performance(client: TestClient, admin_auth_headers: dict):
    response = client.get("/api/v1/institution/department-performance", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_admin_can_access_decision_support(client: TestClient, admin_auth_headers: dict):
    response = client.get("/api/v1/institution/decision-support", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "risk_signals" in data
    assert "recommendations" in data

def test_student_cannot_access_decision_support(client: TestClient, student_auth_headers: dict):
    response = client.get("/api/v1/institution/decision-support", headers=student_auth_headers)
    assert response.status_code == 403
