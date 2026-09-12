from fastapi import APIRouter
from models.schemas import LoginRequest, TokenResponse
from services.auth_service import auth_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
router_v1 = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
@router_v1.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    """
    Authenticates a known identity and issues a server-scoped JWT.
    Delegates validation and token generation to AuthService.
    """
    return auth_service.authenticate_user(request)
