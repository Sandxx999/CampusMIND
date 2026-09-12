from fastapi import APIRouter, HTTPException, status
from models.schemas import LoginRequest, TokenResponse, UserSchema
from auth.jwt_handler import create_access_token
from config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Development-only identities. Production authentication intentionally fails closed
# until an institutional identity provider is integrated in a later phase.
DEMO_USERS = {
    "student1": {"role": "student", "enrollment_no": "2024IFHE001"},
    "faculty1": {"role": "faculty", "enrollment_no": None},
    "admin1": {"role": "admin", "enrollment_no": None},
}

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    """
    Authenticates a known development identity and issues a server-scoped JWT.
    """
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

    # The role and enrollment scope are selected exclusively from the server record.
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
        )
    )
