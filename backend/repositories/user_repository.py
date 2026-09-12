"""
User Data Repository for CampusMIND 2.0.
Encapsulates user identity, role mapping, and user status persistence operations.
"""
from typing import Optional, Dict, Any, List
from sqlalchemy import select
from db.session import get_db_session
from db.models import User, Role, StudentProfile, FacultyProfile, AdminProfile


class UserRepository:
    """Repository handling database persistence operations for user identities and roles."""

    def __init__(self, db_url_provider=None):
        self.db_url_provider = db_url_provider

    def _get_db_url(self) -> Optional[str]:
        return self.db_url_provider() if callable(self.db_url_provider) else None

    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Retrieves user entity by username, including role and profile associations."""
        with get_db_session(database_url=self._get_db_url()) as session:
            stmt = select(User).where(User.username == username.strip())
            user = session.scalars(stmt).first()
            if not user:
                return None

            role_name = user.role.name if user.role else "student"
            enrollment_no = None
            if user.student_profile:
                enrollment_no = user.student_profile.enrollment_no

            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "display_name": user.display_name,
                "role": role_name,
                "status": user.status,
                "enrollment_no": enrollment_no,
            }

    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves user entity by primary key ID."""
        with get_db_session(database_url=self._get_db_url()) as session:
            user = session.get(User, user_id)
            if not user:
                return None

            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "display_name": user.display_name,
                "role": user.role.name if user.role else "student",
                "status": user.status,
            }


user_repository = UserRepository()
