from fastapi import APIRouter, Depends
from auth.rbac import get_current_user
from models.schemas import ChatRequest, ChatResponse, FeedbackRequest, UserSchema
from services.chat_service import chat_service

router = APIRouter(prefix="/api/chat", tags=["Chat & RAG"])
router_v1 = APIRouter(prefix="/api/v1/chat", tags=["Chat & RAG"])


@router.post("", response_model=ChatResponse)
@router_v1.post("", response_model=ChatResponse)
def handle_chat(request: ChatRequest, user: UserSchema = Depends(get_current_user)):
    """
    RAG Chat endpoint:
    Processes query via ChatService (rate limiting, vector retrieval, DB grounding, LLM synthesis, audit logging).
    """
    return chat_service.process_chat_query(request, user)


@router.post("/feedback")
@router_v1.post("/feedback")
def submit_feedback(request: FeedbackRequest, user: UserSchema = Depends(get_current_user)):
    """Logs user thumbs-up/down feedback for query evaluation."""
    return chat_service.submit_feedback(request, user)
