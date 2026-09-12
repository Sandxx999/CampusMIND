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


# Academic Domain Schemas
class AcademicTermSchema(BaseModel):
    id: str
    code: str
    name: str
    academic_year: str
    semester: int
    is_current: bool


class AcademicTermCreateRequest(BaseModel):
    code: str = Field(..., example="2025-SPRING")
    name: str = Field(..., example="Spring 2025 Semester")
    academic_year: str = Field(..., example="2024-2025")
    semester: int = Field(..., ge=1, le=8, example=2)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False


class CourseOfferingSchema(BaseModel):
    id: str
    course_id: str
    course_code: Optional[str] = None
    course_title: Optional[str] = None
    term_id: str
    term_code: Optional[str] = None
    section: str
    room: Optional[str] = None
    schedule: Optional[str] = None
    max_capacity: int
    faculty_name: Optional[str] = None
    status: str


class CourseOfferingListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    offerings: List[CourseOfferingSchema]


# Attendance Domain Schemas
class AttendanceItemSchema(BaseModel):
    student_profile_id: Optional[str] = None
    enrollment_no: Optional[str] = None
    date: Optional[str] = None
    status: str = Field(..., example="present")
    remarks: Optional[str] = None


class AttendanceBulkCreateRequest(BaseModel):
    records: List[AttendanceItemSchema]


class AttendanceSummarySchema(BaseModel):
    student_profile_id: str
    total_classes: int
    attended_classes: int
    attendance_pct: float


class AttendanceRecordSchema(BaseModel):
    id: str
    student_profile_id: str
    course_offering_id: Optional[str] = None
    course_title: Optional[str] = None
    date: str
    status: str
    remarks: Optional[str] = None


class AttendanceResponse(BaseModel):
    enrollment_no: str
    student_name: Optional[str] = None
    summary: AttendanceSummarySchema
    records: List[AttendanceRecordSchema]


# Assessment Domain Schemas
class AssessmentCreateRequest(BaseModel):
    title: str = Field(..., example="Midterm Examination")
    assessment_type: str = Field(..., example="midterm")
    max_marks: float = Field(..., gt=0, example=100.0)
    weightage: float = Field(100.0, ge=0, le=100.0, example=30.0)
    assessment_date: Optional[str] = None
    course_offering_id: Optional[str] = None
    course_id: Optional[str] = None
    status: str = "published"


class AssessmentSchema(BaseModel):
    id: str
    title: str
    assessment_type: str
    max_marks: float
    weightage: float
    status: str


class GradeItemSchema(BaseModel):
    student_profile_id: Optional[str] = None
    enrollment_no: Optional[str] = None
    obtained_marks: float
    grade: Optional[str] = None
    feedback: Optional[str] = None



class GradeBulkCreateRequest(BaseModel):
    grades: List[GradeItemSchema]


class StudentGradeResultSchema(BaseModel):
    id: str
    assessment_id: str
    assessment_title: Optional[str] = None
    assessment_type: Optional[str] = None
    max_marks: Optional[float] = None
    obtained_marks: float
    percentage: float
    grade: Optional[str] = None
    feedback: Optional[str] = None


class StudentAssessmentResultsResponse(BaseModel):
    enrollment_no: str
    student_name: Optional[str] = None
    total_assessments: int
    results: List[StudentGradeResultSchema]


# Announcement Schemas
class AnnouncementCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, example="Midterm Exam Schedule")
    content: str = Field(..., min_length=5, example="Timetable for midterm examinations is released.")
    audience: str = Field("all", example="all")
    department_id: Optional[str] = None
    priority: str = Field("normal", example="normal")


class AnnouncementSchema(BaseModel):
    id: str
    title: str
    content: str
    author_name: Optional[str] = None
    audience: str
    priority: str
    created_at: str


class AnnouncementListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    announcements: List[AnnouncementSchema]


# Campus Event Schemas
class EventCreateRequest(BaseModel):
    title: str = Field(..., example="Campus AI Workshop")
    description: str = Field(..., example="Hands-on machine learning session.")
    location: str = Field(..., example="Main Auditorium")
    start_time: str
    end_time: str
    audience: str = Field("all", example="all")
    category: str = Field("general", example="workshop")
    capacity: Optional[int] = None
    requires_registration: bool = False


class CampusEventSchema(BaseModel):
    id: str
    title: str
    description: str
    location: str
    start_time: str
    end_time: str
    organizer_name: Optional[str] = None
    category: str
    capacity: Optional[int] = None
    requires_registration: bool
    status: str


class EventListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    events: List[CampusEventSchema]


# Knowledge Document Schemas
class KnowledgeDocumentCreateRequest(BaseModel):
    title: str = Field(..., example="Academic Regulations 2024-25")
    file_path: str = Field(..., example="data/academic_rules.txt")
    category: str = Field("general", example="policy")
    department_id: Optional[str] = None
    audience: str = Field("all", example="all")
    version: str = Field("1.0", example="1.0")


class KnowledgeDocumentSchema(BaseModel):
    id: str
    title: str
    file_path: str
    category: str
    audience: str
    version: str
    chunk_count: int
    is_active: bool
    created_at: str


class KnowledgeDocumentListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    documents: List[KnowledgeDocumentSchema]


# Unified Search Schemas
class UnifiedSearchResponse(BaseModel):
    query: str
    courses: List[dict]
    announcements: List[dict]
    events: List[dict]
    documents: List[dict]
