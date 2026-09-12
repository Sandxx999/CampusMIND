"""
Authentication Service.
Encapsulates user authentication, demo identity management, and JWT token issuance.
"""
from fastapi import HTTPException, status
from auth.jwt_handler import create_access_token
from core.config import settings
from models.schemas import LoginRequest, TokenResponse, UserSchema

DEMO_USERS = {
    "student1": {"role": "student", "enrollment_no": "2024IFHE001"},
    "faculty1": {"role": "faculty", "enrollment_no": None},
    "admin1": {"role": "admin", "enrollment_no": None},
}


class AuthService:
    """Service class managing login and credential validation."""

    def authenticate_user(self, request: LoginRequest) -> TokenResponse:
        """Validates login credentials and returns signed access token and user metadata."""
        if not settings.DEMO_MODE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Production authentication is not configured. Demo authentication is disabled.",
            )

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
