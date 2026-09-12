"""Knowledge Foundation Service for CampusMIND 2.0.

Implements business logic for managing knowledge document metadata prepared for production RAG.
"""
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from db.session import get_db_session
from db.models import User, KnowledgeDocument
from models.schemas import UserSchema
from repositories.knowledge_repository import knowledge_repository
from repositories.audit_repository import audit_repository


class KnowledgeService:
    def create_document(self, user: UserSchema, data: Dict[str, Any]) -> Dict[str, Any]:
        """Registers metadata for a new knowledge document. Restricted to Faculty and Admin."""
        if user.role == "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students are not authorized to upload knowledge documents."
            )

        with get_db_session() as session:
            actor = session.query(User).filter(User.username == user.username).first()
            doc_data = {
                "title": data["title"],
                "file_path": data["file_path"],
                "category": data.get("category", "general"),
                "department_id": data.get("department_id"),
                "audience": data.get("audience", "all"),
                "version": data.get("version", "1.0"),
                "effective_date": data.get("effective_date"),
                "expiry_date": data.get("expiry_date"),
                "is_active": data.get("is_active", True),
                "checksum": data.get("checksum"),
                "chunk_count": data.get("chunk_count", 0),
                "uploader_id": actor.id if actor else "usr_admin1",
            }
            doc = knowledge_repository.create_document(session, doc_data)

            audit_repository.log_audit_event(
                event_type="KNOWLEDGE_DOC_CREATED",
                actor_username=user.username,
                user_id=actor.id if actor else None,
                details=f"Registered knowledge document '{doc.title}' (Category: {doc.category})"
            )

            return {
                "id": doc.id,
                "title": doc.title,
                "file_path": doc.file_path,
                "category": doc.category,
                "audience": doc.audience,
                "version": doc.version,
                "chunk_count": doc.chunk_count,
                "is_active": doc.is_active,
                "created_at": doc.created_at.isoformat() if hasattr(doc.created_at, "isoformat") else str(doc.created_at),
            }


    def list_documents(
        self,
        user: UserSchema,
        category: Optional[str] = None,
        department_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Lists knowledge documents accessible to the user's role."""
        audience_filter = ["all"]
        if user.role == "student":
            audience_filter.append("students")
        elif user.role == "faculty":
            audience_filter.extend(["faculty", "students"])
        elif user.role == "admin":
            audience_filter.extend(["admin", "faculty", "students"])

        with get_db_session() as session:
            docs = knowledge_repository.list_documents(
                session,
                audience_filter=audience_filter,
                category=category,
                department_id=department_id,
                is_active=True,
                limit=limit,
                offset=offset,
            )
            total = knowledge_repository.count_documents(
                session,
                audience_filter=audience_filter,
                category=category,
                department_id=department_id,
                is_active=True,
            )

            results = [
                {
                    "id": d.id,
                    "title": d.title,
                    "file_path": d.file_path,
                    "category": d.category,
                    "audience": d.audience,
                    "version": d.version,
                    "chunk_count": d.chunk_count,
                    "is_active": d.is_active,
                    "created_at": d.created_at.isoformat() if hasattr(d.created_at, "isoformat") else str(d.created_at),
                }
                for d in docs
            ]

            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "documents": results,
            }


knowledge_service = KnowledgeService()
