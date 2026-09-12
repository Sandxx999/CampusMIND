from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any


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


class StudentSchema(BaseModel):
    enrollment_no: str
    name: str
    email: str
    mobile_no: str
    branch: str
    year: int
    semester: int
    courses_enrolled: str
    sgpa: float
    cgpa: float
    attendance_pct: float
    backlogs: int
    fee_status: str


class StudentListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    students: List[StudentSchema]


class StudentStatsSummary(BaseModel):
    total_students: int
    avg_cgpa: float
    avg_attendance_pct: float
    total_backlogs: int
    branch_distribution: dict
    fee_status_breakdown: dict


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


class HealthCheckResponse(BaseModel):
    status: str = "healthy"
    service: str = "CampusMind RAG Assistant"
    version: str = "2.0.0"
    environment: str


class ReadinessCheckResponse(BaseModel):
    status: str = "ready"
    database: str = "connected"
    chroma_db: str = "connected"
    details: Dict[str, Any] = {}


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    detail: str
    error: Optional[ErrorDetail] = None
