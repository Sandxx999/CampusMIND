"""
Versioned API Router for Phase 6 Single Sign-On (SSO / OIDC).
"""
from fastapi import APIRouter, Depends
from auth.rbac import get_current_user, require_role
from models.schemas import SSOConfigSchema, SSOLoginRequest, TokenResponse, UserSchema
from services.sso_service import sso_service

router_v1 = APIRouter(prefix="/api/v1/auth/sso", tags=["Phase 6 Single Sign-On"])


@router_v1.get("/config", response_model=SSOConfigSchema)
def get_sso_config():
    """Returns active institutional Single Sign-On configuration."""
    return sso_service.get_sso_config()


@router_v1.put("/config", response_model=SSOConfigSchema)
def update_sso_config(
    provider_name: str,
    issuer_url: str,
    client_id: str,
    is_active: bool = True,
    allow_jit_provisioning: bool = True,
    user: UserSchema = Depends(require_role(["admin"])),
):
    """Updates institutional Single Sign-On configuration. Restricted to Admin role."""
    return sso_service.update_sso_config(
        provider_name=provider_name,
        issuer_url=issuer_url,
        client_id=client_id,
        is_active=is_active,
        allow_jit_provisioning=allow_jit_provisioning,
        actor_username=user.username,
    )


@router_v1.post("/login", response_model=TokenResponse)
def sso_login(request: SSOLoginRequest):
    """Authenticates an OIDC/SAML token assertion and returns a signed access token."""
    return sso_service.authenticate_sso(request)
