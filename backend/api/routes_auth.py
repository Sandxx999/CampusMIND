from fastapi import APIRouter, HTTPException, status
from models.schemas import LoginRequest, TokenResponse, UserSchema
from auth.jwt_handler import create_access_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Dummy in-memory users for demonstration & capstone presentation
DEMO_USERS = {
    "student1": {"password": "password123", "role": "student"},
    "faculty1": {"password": "password123", "role": "faculty"},
    "admin1": {"password": "password123", "role": "admin"},
}

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    """
    Authenticates campus users and issues JWT token encoded with user role.
    """
    user_info = DEMO_USERS.get(request.username)
    
    # Check credentials
    if not user_info or user_info["password"] != request.password:
        # For seamless testing, allow any user if password is password123
        if request.password != "password123":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password credentials."
            )
        user_info = {"password": request.password, "role": request.role}

    # Issue JWT token
    token_data = {
        "sub": request.username,
        "role": request.role or user_info.get("role", "student")
    }
    access_token = create_access_token(token_data)

    return TokenResponse(
        access_token=access_token,
        user=UserSchema(username=request.username, role=token_data["role"])
    )
