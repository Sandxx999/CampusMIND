"""
Knowledge Foundation Service for CampusMIND 2.0.

Implements business logic for document ingestion, version lifecycle tracking,
active/inactive status management, and vector store index synchronization.
"""
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from db.session import get_db_session
from db.models import User, KnowledgeDocument
from models.schemas import UserSchema
from repositories.knowledge_repository import knowledge_repository
from repositories.audit_repository import audit_repository
from rag.ingest import DocumentIngestionEngine
from rag.vector_store import get_vector_store


class KnowledgeService:
    def create_document(self, user: UserSchema, data: Dict[str, Any]) -> Dict[str, Any]:
        """Registers metadata for a new knowledge document and triggers ingestion. Restricted to Faculty and Admin."""
        if user.role == "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students are not authorized to upload or ingest knowledge documents."
            )

        file_path = data["file_path"]
        engine = DocumentIngestionEngine()
        ingest_res = engine.ingest_single_document(file_path, force=True)

        if ingest_res.get("status") == "failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document ingestion failed: {ingest_res.get('error')}"
            )

        with get_db_session() as session:
            doc = knowledge_repository.get_document_by_id(session, ingest_res.get("document_id", ""))
            if not doc:
                doc = session.query(KnowledgeDocument).filter(KnowledgeDocument.file_path == file_path).first()
            if doc and data.get("title"):
                doc.title = data["title"]

            actor = session.query(User).filter(User.username == user.username).first()

            audit_repository.log_audit_event(
                event_type="KNOWLEDGE_DOC_CREATED",
                actor_username=user.username,
                user_id=actor.id if actor else None,
                details=f"Registered and ingested document '{data['title']}' (Category: {data.get('category', 'general')})"
            )

            return {
                "id": doc.id if doc else ingest_res.get("document_id", "doc_new"),
                "title": doc.title if doc else data["title"],
                "file_path": doc.file_path if doc else file_path,
                "category": doc.category if doc else data.get("category", "general"),
                "audience": doc.audience if doc else data.get("audience", "all"),
                "version": doc.version if doc else data.get("version", "1.0"),
                "chunk_count": doc.chunk_count if doc else ingest_res.get("chunk_count", 0),
                "is_active": doc.is_active if doc else True,
                "created_at": doc.created_at.isoformat() if doc and hasattr(doc.created_at, "isoformat") else str(doc.created_at if doc else ""),
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
                is_active=None if user.role in {"faculty", "admin"} else True,
                limit=limit,
                offset=offset,
            )
            total = knowledge_repository.count_documents(
                session,
                audience_filter=audience_filter,
                category=category,
                department_id=department_id,
                is_active=None if user.role in {"faculty", "admin"} else True,
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

    def get_document(self, user: UserSchema, doc_id: str) -> Dict[str, Any]:
        """Retrieves metadata and status for a specific knowledge document."""
        with get_db_session() as session:
            doc = knowledge_repository.get_document_by_id(session, doc_id)
            if not doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Knowledge document '{doc_id}' not found."
                )

            # Check role permission
            if user.role == "student" and doc.audience not in {"all", "student", "students"}:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to view this document."
                )

            return {
                "id": doc.id,
                "title": doc.title,
                "file_path": doc.file_path,
                "category": doc.category,
                "audience": doc.audience,
                "version": doc.version,
                "checksum": doc.checksum,
                "chunk_count": doc.chunk_count,
                "is_active": doc.is_active,
                "created_at": doc.created_at.isoformat() if hasattr(doc.created_at, "isoformat") else str(doc.created_at),
                "updated_at": doc.updated_at.isoformat() if hasattr(doc.updated_at, "isoformat") else str(doc.updated_at),
            }

    def set_document_active_status(self, user: UserSchema, doc_id: str, is_active: bool) -> Dict[str, Any]:
        """Deactivates or reactivates a knowledge document. Restricted to Faculty and Admin."""
        if user.role == "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students are not authorized to modify knowledge document status."
            )

        with get_db_session() as session:
            doc = knowledge_repository.update_document(session, doc_id, {"is_active": is_active})
            if not doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Knowledge document '{doc_id}' not found."
                )

            # Synchronize vector store
            vector_store = get_vector_store()
            if not is_active:
                vector_store.delete_document_chunks(doc_id)
                vector_store.delete_document_chunks(doc.title)

            actor = session.query(User).filter(User.username == user.username).first()
            action_name = "KNOWLEDGE_DOC_ACTIVATED" if is_active else "KNOWLEDGE_DOC_DEACTIVATED"
            audit_repository.log_audit_event(
                event_type=action_name,
                actor_username=user.username,
                user_id=actor.id if actor else None,
                details=f"{'Activated' if is_active else 'Deactivated'} knowledge document '{doc.title}' (ID: {doc.id})"
            )

            return {
                "id": doc.id,
                "title": doc.title,
                "is_active": doc.is_active,
                "message": f"Document successfully {'activated' if is_active else 'deactivated'}."
            }

    def sync_vector_index(self, user: UserSchema) -> Dict[str, Any]:
        """Triggers full vector database re-synchronization with active raw campus documents."""
        if user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vector index synchronization is restricted to administrators."
            )

        engine = DocumentIngestionEngine()
        results = engine.ingest_directory()

        with get_db_session() as session:
            actor = session.query(User).filter(User.username == user.username).first()
            audit_repository.log_audit_event(
                event_type="VECTOR_INDEX_SYNCHRONIZED",
                actor_username=user.username,
                user_id=actor.id if actor else None,
                details=f"Admin triggered vector index sync. Processed {len(results)} documents."
            )

        return {
            "status": "success",
            "processed_documents_count": len(results),
            "results": results,
        }


knowledge_service = KnowledgeService()
