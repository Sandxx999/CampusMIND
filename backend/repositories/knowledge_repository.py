"""Knowledge Repository for CampusMIND 2.0.

Provides database access for knowledge document metadata and RAG preparedness.
"""
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from db.models import KnowledgeDocument, Department, User


class KnowledgeRepository:
    def create_document(self, db: Session, data: Dict[str, Any]) -> KnowledgeDocument:
        """Creates a new knowledge document metadata record."""
        doc = KnowledgeDocument(
            id=data.get("id", f"doc_{uuid.uuid4().hex[:12]}"),
            title=data["title"],
            file_path=data["file_path"],
            category=data.get("category", "general"),
            department_id=data.get("department_id"),
            audience=data.get("audience", "all"),
            version=data.get("version", "1.0"),
            effective_date=data.get("effective_date"),
            expiry_date=data.get("expiry_date"),
            is_active=data.get("is_active", True),
            checksum=data.get("checksum"),
            chunk_count=data.get("chunk_count", 0),
            uploader_id=data.get("uploader_id"),
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    def get_document_by_id(self, db: Session, doc_id: str) -> Optional[KnowledgeDocument]:
        """Retrieves a knowledge document by ID."""
        return db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()

    def list_documents(
        self,
        db: Session,
        audience_filter: Optional[List[str]] = None,
        category: Optional[str] = None,
        department_id: Optional[str] = None,
        is_active: Optional[bool] = True,
        limit: int = 50,
        offset: int = 0,
    ) -> List[KnowledgeDocument]:
        """Lists knowledge documents matching filters."""
        query = db.query(KnowledgeDocument)
        if is_active is not None:
            query = query.filter(KnowledgeDocument.is_active == is_active)
        if category:
            query = query.filter(KnowledgeDocument.category == category)
        if department_id:
            query = query.filter(or_(
                KnowledgeDocument.department_id == department_id,
                KnowledgeDocument.department_id.is_(None)
            ))
        if audience_filter:
            query = query.filter(or_(
                KnowledgeDocument.audience.in_(audience_filter),
                KnowledgeDocument.audience == "all"
            ))
        return query.order_by(KnowledgeDocument.created_at.desc()).offset(offset).limit(limit).all()

    def count_documents(
        self,
        db: Session,
        audience_filter: Optional[List[str]] = None,
        category: Optional[str] = None,
        department_id: Optional[str] = None,
        is_active: Optional[bool] = True,
    ) -> int:
        """Counts knowledge documents matching filters."""
        query = db.query(func.count(KnowledgeDocument.id))
        if is_active is not None:
            query = query.filter(KnowledgeDocument.is_active == is_active)
        if category:
            query = query.filter(KnowledgeDocument.category == category)
        if department_id:
            query = query.filter(or_(
                KnowledgeDocument.department_id == department_id,
                KnowledgeDocument.department_id.is_(None)
            ))
        if audience_filter:
            query = query.filter(or_(
                KnowledgeDocument.audience.in_(audience_filter),
                KnowledgeDocument.audience == "all"
            ))
        return query.scalar() or 0

    def update_document(self, db: Session, doc_id: str, updates: Dict[str, Any]) -> Optional[KnowledgeDocument]:
        """Updates a knowledge document record."""
        doc = self.get_document_by_id(db, doc_id)
        if not doc:
            return None
        for k, v in updates.items():
            if hasattr(doc, k) and v is not None:
                setattr(doc, k, v)
        db.commit()
        db.refresh(doc)
        return doc


knowledge_repository = KnowledgeRepository()
