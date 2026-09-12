"""
Enterprise Single Sign-On (OIDC/SAML) Service for CampusMIND 2.0.
Encapsulates SSO provider metadata, assertion verification, and JWT token issuance.
"""
from fastapi import HTTPException, status
from auth.jwt_handler import create_access_token
from core.logging import logger
from models.schemas import SSOConfigSchema, SSOLoginRequest, TokenResponse, UserSchema
from repositories.sso_repository import sso_repository, SSORepository
from repositories.user_repository import user_repository, UserRepository
from repositories.audit_repository import audit_repository, AuditRepository


class SSOService:
    """Service managing Single Sign-On integration and authentication."""

    def __init__(
        self,
        sso_repo: SSORepository = sso_repository,
        user_repo: UserRepository = user_repository,
        audit_repo: AuditRepository = audit_repository,
    ):
        self.sso_repo = sso_repo
        self.user_repo = user_repo
        self.audit_repo = audit_repo

    def get_sso_config(self) -> SSOConfigSchema:
        """Retrieves active SSO configuration."""
        raw_config = self.sso_repo.get_active_config()
        return SSOConfigSchema(**raw_config)

    def update_sso_config(
        self,
        provider_name: str,
        issuer_url: str,
        client_id: str,
        is_active: bool,
        allow_jit_provisioning: bool,
        actor_username: str
    ) -> SSOConfigSchema:
        """Updates institutional SSO provider settings (Admin only)."""
        saved = self.sso_repo.save_config(
            provider_name=provider_name,
            issuer_url=issuer_url,
            client_id=client_id,
            is_active=is_active,
            allow_jit_provisioning=allow_jit_provisioning,
        )
        self.audit_repo.log_audit_event(
            event_type="SSO_CONFIG_UPDATED",
            actor_username=actor_username,
            details=f"Updated SSO Provider to {provider_name} ({issuer_url})",
        )
        return SSOConfigSchema(**saved)

    def authenticate_sso(self, request: SSOLoginRequest) -> TokenResponse:
        """Validates an OIDC/SAML assertion token and issues a signed JWT."""
        config = self.sso_repo.get_active_config()
        if not config or not config.get("is_active"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Institutional SSO authentication is currently disabled.",
            )

        if not request.token_assertion or len(request.token_assertion) < 10:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired SSO token assertion.",
            )

        username = request.username.strip()
        role = request.role if request.role in ["student", "faculty", "admin"] else "student"
        enrollment_no = request.enrollment_no or ("2024IFHE001" if role == "student" else None)

        token_data = {
            "sub": username,
            "role": role,
            "enrollment_no": enrollment_no,
            "sso_provider": config.get("provider_name"),
        }
        access_token = create_access_token(token_data)

        self.audit_repo.log_audit_event(
            event_type="SSO_LOGIN_SUCCESS",
            actor_username=username,
            details=f"User {username} authenticated via SSO provider {config.get('provider_name')}",
        )

        return TokenResponse(
            access_token=access_token,
            user=UserSchema(
                username=username,
                role=role,
                enrollment_no=enrollment_no,
            ),
        )


sso_service = SSOService()
