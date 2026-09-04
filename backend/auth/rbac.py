from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth.jwt_handler import decode_access_token
from models.schemas import UserSchema

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserSchema:
    """
    FastAPI dependency to extract and verify the JWT user payload from HTTP Bearer headers.
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload or "sub" not in payload or "role" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token or session expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return UserSchema(username=payload["sub"], role=payload["role"])

def require_role(allowed_roles: list):
    """
    Factory dependency for role-based authorization checking.
    Ensures strict server-side scoping for student/faculty/admin routes.
    """
    def role_checker(user: UserSchema = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Role '{user.role}' is not authorized for this resource."
            )
        return user
    return role_checker
