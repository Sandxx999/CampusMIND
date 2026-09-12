from fastapi import APIRouter, Depends
from auth.rbac import require_role
from models.schemas import AdminStatsResponse, UserSchema
from services.admin_service import admin_service

router = APIRouter(prefix="/api/admin", tags=["Admin Analytics"])
router_v1 = APIRouter(prefix="/api/v1/admin", tags=["Admin Analytics"])


@router.get("/stats", response_model=AdminStatsResponse)
@router_v1.get("/stats", response_model=AdminStatsResponse)
def get_admin_stats(user: UserSchema = Depends(require_role(["admin"]))):
    """
    Returns aggregated RAG metrics: total queries, latency, failure rates, top topics, feedback.
    Restricted to Admin role only via RBAC middleware.
    """
    return admin_service.get_admin_stats()
