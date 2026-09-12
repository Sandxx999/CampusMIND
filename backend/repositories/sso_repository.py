"""
SSO Provider Configuration Data Repository for CampusMIND 2.0.
Encapsulates CRUD operations for institutional Single Sign-On (OIDC/SAML) provider settings.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import select
from db.session import get_db_session
from db.models import SSOProviderConfig, utc_now
from core.logging import logger


class SSORepository:
    """Repository managing SSO Provider Configurations."""

    def get_active_config(self) -> Optional[Dict[str, Any]]:
        """Retrieves the active SSO provider configuration."""
        try:
            with get_db_session() as session:
                config = session.execute(
                    select(SSOProviderConfig).where(SSOProviderConfig.is_active == True)
                ).scalar_one_or_none()
                if config:
                    return {
                        "id": config.id,
                        "provider_name": config.provider_name,
                        "issuer_url": config.issuer_url,
                        "client_id": config.client_id,
                        "is_active": config.is_active,
                        "allow_jit_provisioning": config.allow_jit_provisioning,
                        "created_at": config.created_at.isoformat() if hasattr(config.created_at, "isoformat") else str(config.created_at),
                        "updated_at": config.updated_at.isoformat() if hasattr(config.updated_at, "isoformat") else str(config.updated_at),
                    }
        except Exception as e:
            logger.debug(f"Failed to fetch active SSO config from DB: {e}")

        # Fallback default configuration for campus identity provider
        return {
            "id": "sso_ifhe_oidc",
            "provider_name": "IFHE Institutional Identity Provider (OIDC)",
            "issuer_url": "https://auth.ifheindia.org/oidc",
            "client_id": "campusmind_app_client",
            "is_active": True,
            "allow_jit_provisioning": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def save_config(
        self,
        provider_name: str,
        issuer_url: str,
        client_id: str,
        is_active: bool = True,
        allow_jit_provisioning: bool = True,
        config_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Saves or updates an SSO provider configuration."""
        config_id = config_id or f"sso_{uuid.uuid4().hex[:8]}"
        now = utc_now()
        try:
            with get_db_session() as session:
                existing = session.get(SSOProviderConfig, config_id)
                if existing:
                    existing.provider_name = provider_name
                    existing.issuer_url = issuer_url
                    existing.client_id = client_id
                    existing.is_active = is_active
                    existing.allow_jit_provisioning = allow_jit_provisioning
                    existing.updated_at = now
                else:
                    new_config = SSOProviderConfig(
                        id=config_id,
                        provider_name=provider_name,
                        issuer_url=issuer_url,
                        client_id=client_id,
                        is_active=is_active,
                        allow_jit_provisioning=allow_jit_provisioning,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(new_config)
        except Exception as e:
            logger.error(f"Failed to save SSO config in DB: {e}")

        return {
            "id": config_id,
            "provider_name": provider_name,
            "issuer_url": issuer_url,
            "client_id": client_id,
            "is_active": is_active,
            "allow_jit_provisioning": allow_jit_provisioning,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }


sso_repository = SSORepository()
