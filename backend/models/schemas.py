from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional

class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(..., example="student1")
    password: str = Field(..., example="password123")

class UserSchema(BaseModel):
    username: str
    role: str
    enrollment_no: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserSchema

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=1000, example="When is the fee payment deadline?")

class SourceCitation(BaseModel):
    document_name: str
    section: Optional[str] = "General"
    score: float
    snippet: str

class ChatResponse(BaseModel):
    query_id: str
    answer: str
    sources: List[SourceCitation]
    confidence: float
    is_fallback: bool

class FeedbackRequest(BaseModel):
    query_id: str
    is_positive: bool

class AdminTopicCount(BaseModel):
    topic: str
    count: int

class AdminLogEntry(BaseModel):
    query_id: str
    timestamp: str
    username: str
    role: str
    question: str
    latency_ms: float
    chunk_count: int

class AdminStatsResponse(BaseModel):
    total_queries: int
    avg_latency_ms: float
    no_answer_rate: str
    positive_feedback_pct: str
    top_topics: List[AdminTopicCount]
    recent_logs: List[AdminLogEntry]
