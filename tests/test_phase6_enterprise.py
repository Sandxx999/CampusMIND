"""
Phase 6 Enterprise Governance, SSO, & System Test Suite for CampusMIND 2.0.
Verifies Single Sign-On (OIDC), system status telemetry, security audit log querying,
dynamic RAG benchmark execution, report export functionality, and RBAC / IDOR security boundaries.
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from auth.jwt_handler import create_access_token
from services.sso_service import sso_service
from services.system_governance_service import system_governance_service
from services.export_service import export_service

client = TestClient(app)


def get_token(username: str, role: str, enrollment_no: str = None) -> str:
    token_data = {"sub": username, "role": role, "enrollment_no": enrollment_no}
    return create_access_token(token_data)


def test_sso_config_public_endpoint():
    """Verifies that SSO configuration can be retrieved publicly."""
    response = client.get("/api/v1/auth/sso/config")
    assert response.status_code == 200
    data = response.json()
    assert "provider_name" in data
    assert "issuer_url" in data
    assert data["is_active"] is True


def test_sso_login_assertion():
    """Verifies valid OIDC token assertion login."""
    payload = {
        "provider_id": "sso_ifhe_oidc",
        "token_assertion": "valid_oidc_mock_token_assertion_123456",
        "username": "student1",
        "email": "student1@ifheindia.org",
        "role": "student",
        "enrollment_no": "2024IFHE001",
    }
    response = client.post("/api/v1/auth/sso/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == "student1"
    assert data["user"]["role"] == "student"


def test_sso_login_invalid_assertion():
    """Verifies rejection of invalid SSO assertion."""
    payload = {
        "provider_id": "sso_ifhe_oidc",
        "token_assertion": "short",
        "username": "student1",
        "email": "student1@ifheindia.org",
    }
    response = client.post("/api/v1/auth/sso/login", json=payload)
    assert response.status_code == 401


def test_system_status_admin_only():
    """Verifies that detailed system status is restricted to Admin role."""
    student_token = get_token("student1", "student", "2024IFHE001")
    admin_token = get_token("admin1", "admin")

    # Forbidden for student
    res_student = client.get(
        "/api/v1/admin/governance/system-status",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_student.status_code == 403

    # Permitted for admin
    res_admin = client.get(
        "/api/v1/admin/governance/system-status",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == 200
    data = res_admin.json()
    assert data["status"] == "operational"
    assert "database" in data
    assert "vector_store" in data


def test_audit_events_admin_only():
    """Verifies security audit log querying is restricted to Admin role."""
    student_token = get_token("student1", "student", "2024IFHE001")
    admin_token = get_token("admin1", "admin")

    # Student forbidden
    res_student = client.get(
        "/api/v1/admin/governance/audit-events",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_student.status_code == 403

    # Admin allowed
    res_admin = client.get(
        "/api/v1/admin/governance/audit-events",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == 200
    data = res_admin.json()
    assert "events" in data
    assert isinstance(data["events"], list)


def test_rag_eval_benchmark_endpoint():
    """Verifies execution of dynamic RAG evaluator benchmark endpoint."""
    admin_token = get_token("admin1", "admin")
    response = client.post(
        "/api/v1/admin/governance/eval",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "context_precision" in data
    assert "faithfulness" in data
    assert data["context_precision"] >= 0.0
    assert data["context_precision"] <= 1.0


def test_trigger_reindex_task():
    """Verifies background vector store re-indexing trigger and task tracking."""
    admin_token = get_token("admin1", "admin")
    response = client.post(
        "/api/v1/admin/governance/reindex",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    task_data = response.json()
    assert "id" in task_data
    assert task_data["task_type"] == "VECTOR_REINDEX"

    # Fetch task status
    task_id = task_data["id"]
    res_task = client.get(
        f"/api/v1/admin/governance/tasks/{task_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_task.status_code == 200
    assert res_task.json()["id"] == task_id


def test_export_student_report():
    """Verifies official student academic audit report generation."""
    student_token = get_token("student1", "student", "2024IFHE001")
    response = client.get(
        "/api/v1/export/student/me",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["report_type"] == "STUDENT_ACADEMIC_AUDIT"
    assert "checksum" in data
    assert "2024IFHE001" in data["content"]


def test_export_admin_report():
    """Verifies institutional overview report export for admin."""
    admin_token = get_token("admin1", "admin")
    response = client.get(
        "/api/v1/export/admin/overview",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["report_type"] == "INSTITUTIONAL_OVERVIEW"
    assert "checksum" in data


def test_export_student_report_forbidden_for_admin():
    """Verifies admin role cannot call student-specific /me report export without student identity."""
    admin_token = get_token("admin1", "admin")
    response = client.get(
        "/api/v1/export/student/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 403
