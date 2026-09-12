"""
Authentication Service for CampusMIND 2.0.
Encapsulates user authentication, institutional identity lookup, and JWT token issuance.
Prepared for future OIDC/SSO institutional identity integration.
"""
from fastapi import HTTPException, status
from auth.jwt_handler import create_access_token
from core.config import settings
from models.schemas import LoginRequest, TokenResponse, UserSchema
from repositories.user_repository import user_repository, UserRepository

DEMO_USERS = {
    "student1": {"role": "student", "enrollment_no": "2024IFHE001"},
    "faculty1": {"role": "faculty", "enrollment_no": None},
    "admin1": {"role": "admin", "enrollment_no": None},
}


class AuthService:
    """Service class managing login, identity resolution, and credential validation."""

    def __init__(self, user_repo: UserRepository = user_repository):
        self.user_repo = user_repo

    def authenticate_user(self, request: LoginRequest) -> TokenResponse:
        """Validates login credentials and returns signed access token and user metadata."""
        if not settings.DEMO_MODE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Production authentication is not configured. Demo authentication is disabled.",
            )

        user_info = None
        try:
            db_user = self.user_repo.get_by_username(request.username)
            if db_user:
                if db_user.get("status") != "active":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="User account is inactive or suspended.",
                    )
                user_info = {
                    "role": db_user["role"],
                    "enrollment_no": db_user["enrollment_no"],
                }
        except HTTPException:
            raise
        except Exception:
            pass

        if not user_info:
            user_info = DEMO_USERS.get(request.username)

        if not user_info or request.password != settings.DEMO_PASSWORD:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password credentials.",
            )

        token_data = {
            "sub": request.username,
            "role": user_info["role"],
            "enrollment_no": user_info["enrollment_no"],
        }
        access_token = create_access_token(token_data)

        return TokenResponse(
            access_token=access_token,
            user=UserSchema(
                username=request.username,
                role=user_info["role"],
                enrollment_no=user_info["enrollment_no"],
            ),
        )


auth_service = AuthService()
