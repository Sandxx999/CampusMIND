from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth.jwt_handler import decode_access_token
from models.schemas import UserSchema

security = HTTPBearer(auto_error=False)
VALID_ROLES = {"student", "faculty", "admin"}

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> UserSchema:
    """
    FastAPI dependency to extract and verify the JWT user payload from HTTP Bearer headers.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload or "sub" not in payload or payload.get("role") not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token or session expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return UserSchema(
        username=payload["sub"],
        role=payload["role"],
        enrollment_no=payload.get("enrollment_no"),
    )


def can_access_student_record(user: UserSchema, enrollment_no: str) -> bool:
    """Students can only access their own record; staff access remains role-based."""
    if user.role in {"faculty", "admin"}:
        return True
    return user.role == "student" and bool(user.enrollment_no) and (
        user.enrollment_no.casefold() == enrollment_no.strip().casefold()
    )

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
