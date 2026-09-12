"""
Knowledge Foundation API Routes for CampusMIND 2.0.

Exposes endpoints for knowledge document metadata tracking, document lifecycle management,
activation toggles, and vector synchronization under /api/v1/knowledge.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Path
from auth.rbac import get_current_user, require_role
from models.schemas import (
    KnowledgeDocumentCreateRequest,
    KnowledgeDocumentSchema,
    KnowledgeDocumentListResponse,
    UserSchema,
)
from services.knowledge_service import knowledge_service

router_v1 = APIRouter(prefix="/api/v1/knowledge", tags=["Knowledge & Documents"])


@router_v1.get("", response_model=KnowledgeDocumentListResponse)
def list_knowledge_documents(
    category: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: UserSchema = Depends(get_current_user),
):
    """Lists knowledge document metadata available for the user's role."""
    return knowledge_service.list_documents(
        user=user,
        category=category,
        department_id=department_id,
        limit=limit,
        offset=offset,
    )


@router_v1.post("", response_model=KnowledgeDocumentSchema)
def create_knowledge_document(
    req: KnowledgeDocumentCreateRequest,
    user: UserSchema = Depends(require_role(["faculty", "admin"])),
):
    """Registers metadata for a new campus knowledge document. Restricted to Faculty and Admin."""
    return knowledge_service.create_document(user, req.model_dump())


@router_v1.get("/{doc_id}")
def get_knowledge_document(
    doc_id: str = Path(..., description="Knowledge Document ID"),
    user: UserSchema = Depends(get_current_user),
):
    """Inspects metadata and version details for a specific knowledge document."""
    return knowledge_service.get_document(user, doc_id)


@router_v1.post("/{doc_id}/deactivate")
def deactivate_knowledge_document(
    doc_id: str = Path(..., description="Knowledge Document ID"),
    user: UserSchema = Depends(require_role(["faculty", "admin"])),
):
    """Deactivates a knowledge document and purges its vectors from retrieval. Restricted to Faculty and Admin."""
    return knowledge_service.set_document_active_status(user, doc_id, is_active=False)


@router_v1.post("/{doc_id}/activate")
def activate_knowledge_document(
    doc_id: str = Path(..., description="Knowledge Document ID"),
    user: UserSchema = Depends(require_role(["faculty", "admin"])),
):
    """Reactivates a knowledge document for retrieval. Restricted to Faculty and Admin."""
    return knowledge_service.set_document_active_status(user, doc_id, is_active=True)


@router_v1.post("/sync")
def trigger_vector_index_sync(
    user: UserSchema = Depends(require_role(["admin"])),
):
    """Triggers full vector database re-synchronization. Restricted to Admin."""
    return knowledge_service.sync_vector_index(user)
