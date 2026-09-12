"""
Versioned API Router for Phase 6 System Governance, Security Audits, and RAG Benchmarking.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from auth.rbac import require_role
from models.schemas import (
    AuditEventListResponse,
    DetailedSystemStatusResponse,
    RAGEvalMetricsSchema,
    SystemTaskSchema,
    UserSchema,
)
from services.system_governance_service import system_governance_service

router_v1 = APIRouter(prefix="/api/v1/admin/governance", tags=["Phase 6 System Governance"])


@router_v1.get("/system-status", response_model=DetailedSystemStatusResponse)
def get_system_status(user: UserSchema = Depends(require_role(["admin"]))):
    """Returns detailed enterprise system status, connection pool health, and active worker tasks. Admin only."""
    return system_governance_service.get_system_status()


@router_v1.get("/audit-events", response_model=AuditEventListResponse)
def get_audit_events(
    actor_username: Optional[str] = Query(None, description="Filter by actor username"),
    event_type: Optional[str] = Query(None, description="Filter by security event type"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    user: UserSchema = Depends(require_role(["admin"])),
):
    """Queries security audit trail events. Admin only."""
    return system_governance_service.get_audit_events(
        actor_username=actor_username,
        event_type=event_type,
        limit=limit,
    )


@router_v1.post("/eval", response_model=RAGEvalMetricsSchema)
def run_rag_eval(user: UserSchema = Depends(require_role(["admin"]))):
    """Triggers dynamic RAG evaluation against eval_qa_pairs.json benchmark dataset. Admin only."""
    return system_governance_service.run_rag_evaluation(actor_username=user.username)


@router_v1.post("/reindex", response_model=SystemTaskSchema)
def trigger_vector_reindex(user: UserSchema = Depends(require_role(["admin"]))):
    """Triggers background document ingestion and ChromaDB re-indexing. Admin only."""
    return system_governance_service.trigger_reindex(actor_username=user.username)


@router_v1.get("/tasks/{task_id}", response_model=SystemTaskSchema)
def get_task_status(
    task_id: str,
    user: UserSchema = Depends(require_role(["admin"])),
):
    """Retrieves status of a background task. Admin only."""
    return system_governance_service.get_task_status(task_id)
