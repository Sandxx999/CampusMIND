"""
Phase 6 SSO Security & Forged-Token Test Suite for CampusMIND 2.0.

Covers cryptographic OIDC token assertion verification and server-side role resolution:
A. Forged JWT signature
B. Wrong signing key
C. Wrong issuer
D. Wrong audience
E. Expired token
F. Client-controlled role escalation
G. Forged admin role claim
H. Tampered token
I. OIDC login with invalid/unverified assertion
J. Valid trusted authentication
"""
import jwt
import pytest
from datetime import UTC, datetime, timedelta
from fastapi.testclient import TestClient
from main import app
from core.config import settings
from auth.jwt_handler import create_access_token

client = TestClient(app)

ISSUER = "https://auth.ifheindia.org/oidc"
AUDIENCE = "campusmind_app_client"


def create_mock_oidc_assertion(
    sub: str = "student1",
    iss: str = ISSUER,
    aud: str = AUDIENCE,
    key: str = None,
    expires_delta: timedelta = None,
    extra_claims: dict = None,
) -> str:
    """Helper to generate signed OIDC token assertions for testing."""
    secret = key or settings.JWT_SECRET_KEY
    now = datetime.now(UTC)
    exp = now + (expires_delta if expires_delta is not None else timedelta(minutes=15))
    claims = {
        "sub": sub,
        "iss": iss,
        "aud": aud,
        "exp": exp,
        "iat": now,
    }
    if extra_claims:
        claims.update(extra_claims)
    return jwt.encode(claims, secret, algorithm="HS256")


def test_sso_sec_valid_trusted_authentication():
    """J. Valid trusted authentication succeeds and returns valid access token with server role."""
    valid_assertion = create_mock_oidc_assertion(sub="student1")
    payload = {
        "provider_id": "sso_ifhe_oidc",
        "token_assertion": valid_assertion,
    }
    response = client.post("/api/v1/auth/sso/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == "student1"
    assert data["user"]["role"] == "student"


def test_sso_sec_forged_signature():
    """A. Token with valid claims but forged/invalid signature must fail authentication."""
    valid_assertion = create_mock_oidc_assertion(sub="student1")
    parts = valid_assertion.split(".")
    forged_assertion = f"{parts[0]}.{parts[1]}.invalid_forged_signature_bytes"

    payload = {
        "provider_id": "sso_ifhe_oidc",
        "token_assertion": forged_assertion,
    }
    response = client.post("/api/v1/auth/sso/login", json=payload)
    assert response.status_code == 401


def test_sso_sec_wrong_signing_key():
    """B. Token signed with an untrusted/different signing key must fail authentication."""
    wrong_key_assertion = create_mock_oidc_assertion(sub="student1", key="untrusted_attacker_secret_key_12345")
    payload = {
        "provider_id": "sso_ifhe_oidc",
        "token_assertion": wrong_key_assertion,
    }
    response = client.post("/api/v1/auth/sso/login", json=payload)
    assert response.status_code == 401


def test_sso_sec_wrong_issuer():
    """C. Token assertion with wrong issuer (iss) must fail authentication."""
    wrong_iss_assertion = create_mock_oidc_assertion(sub="student1", iss="https://untrusted-fake-issuer.com/oidc")
    payload = {
        "provider_id": "sso_ifhe_oidc",
        "token_assertion": wrong_iss_assertion,
    }
    response = client.post("/api/v1/auth/sso/login", json=payload)
    assert response.status_code == 401


def test_sso_sec_wrong_audience():
    """D. Token assertion with wrong audience (aud) must fail authentication."""
    wrong_aud_assertion = create_mock_oidc_assertion(sub="student1", aud="malicious_client_app")
    payload = {
        "provider_id": "sso_ifhe_oidc",
        "token_assertion": wrong_aud_assertion,
    }
    response = client.post("/api/v1/auth/sso/login", json=payload)
    assert response.status_code == 401


def test_sso_sec_expired_token():
    """E. Expired token assertion must fail authentication."""
    expired_assertion = create_mock_oidc_assertion(sub="student1", expires_delta=timedelta(seconds=-300))
    payload = {
        "provider_id": "sso_ifhe_oidc",
        "token_assertion": expired_assertion,
    }
    response = client.post("/api/v1/auth/sso/login", json=payload)
    assert response.status_code == 401


def test_sso_sec_client_role_escalation_prevented():
    """F. Student identity submitting role=admin in request body MUST NOT produce admin access."""
    valid_student_assertion = create_mock_oidc_assertion(sub="student1")
    payload = {
        "provider_id": "sso_ifhe_oidc",
        "token_assertion": valid_student_assertion,
        "role": "admin",
    }
    response = client.post("/api/v1/auth/sso/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "student"

    returned_token = data["access_token"]
    admin_check = client.get(
        "/api/v1/admin/governance/system-status",
        headers={"Authorization": f"Bearer {returned_token}"},
    )
    assert admin_check.status_code == 403


def test_sso_sec_forged_admin_role_claim():
    """G. Unregistered identity asserting role=admin in claims MUST NOT grant admin privileges."""
    unregistered_assertion = create_mock_oidc_assertion(
        sub="new_jit_user_99",
        extra_claims={"role": "admin"},
    )
    payload = {
        "provider_id": "sso_ifhe_oidc",
        "token_assertion": unregistered_assertion,
        "role": "admin",
    }
    response = client.post("/api/v1/auth/sso/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["role"] == "student"

    returned_token = data["access_token"]
    admin_check = client.get(
        "/api/v1/admin/governance/system-status",
        headers={"Authorization": f"Bearer {returned_token}"},
    )
    assert admin_check.status_code == 403


def test_sso_sec_tampered_token_payload():
    """H. Modifying payload claims after signing must fail authentication."""
    valid_assertion = create_mock_oidc_assertion(sub="student1")
    parts = valid_assertion.split(".")
    tampered_payload_part = parts[1] + "extra"
    tampered_assertion = f"{parts[0]}.{tampered_payload_part}.{parts[2]}"

    payload = {
        "provider_id": "sso_ifhe_oidc",
        "token_assertion": tampered_assertion,
    }
    response = client.post("/api/v1/auth/sso/login", json=payload)
    assert response.status_code == 401


def test_sso_sec_invalid_unverified_assertion_string():
    """I. Non-JWT arbitrary string assertion must be rejected."""
    payload = {
        "provider_id": "sso_ifhe_oidc",
        "token_assertion": "this_is_not_a_valid_jwt_token_string",
    }
    response = client.post("/api/v1/auth/sso/login", json=payload)
    assert response.status_code == 401
