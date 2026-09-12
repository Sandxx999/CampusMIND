from fastapi import APIRouter, Depends, Request, HTTPException
from auth.rbac import get_current_user
from models.schemas import ChatRequest, ChatResponse, FeedbackRequest, UserSchema
from services.chat_service import chat_service

router = APIRouter(prefix="/api/chat", tags=["Chat & RAG"])
router_v1 = APIRouter(prefix="/api/v1/chat", tags=["Chat & RAG"])


@router.post("", response_model=ChatResponse)
@router_v1.post("", response_model=ChatResponse)
def handle_chat(request_data: ChatRequest, req: Request, user: UserSchema = Depends(get_current_user)):
    """
    RAG Chat endpoint:
    Processes query via ChatService (rate limiting, vector retrieval, DB grounding, LLM synthesis, audit logging).
    """
    if not getattr(req.app.state, "is_ready", True):
        raise HTTPException(
            status_code=503,
            detail="System is currently initializing knowledge base. Please try again in a few minutes."
        )
    return chat_service.process_chat_query(request_data, user)


@router.post("/feedback")
@router_v1.post("/feedback")
def submit_feedback(request: FeedbackRequest, user: UserSchema = Depends(get_current_user)):
    """Logs user thumbs-up/down feedback for query evaluation."""
    return chat_service.submit_feedback(request, user)
