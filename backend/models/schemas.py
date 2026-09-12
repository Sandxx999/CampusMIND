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
    category: Optional[str] = "general"
    version: Optional[str] = "1.0"
    score: float
    snippet: str


class ChatResponse(BaseModel):
    query_id: str
    answer: str
    sources: List[SourceCitation]
    confidence: float
    evidence_quality: str = "high"
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


# Phase 5 Analytics Domain Schemas
class AttendanceRiskSchema(BaseModel):
    risk_level: str
    attendance_percentage: float
    required_percentage: float
    classes_attended: int
    classes_conducted: int
    classes_missed: int
    deficit_percentage: float
    classes_needed_to_recover: int
    is_recoverable: bool
    insufficient_data: bool
    explanation: str


class RecommendationSchema(BaseModel):
    recommendation: str
    reason: str
    supporting_metrics: Dict[str, Any]
    severity: str
    source: str


class StudentAttendanceAnalyticsResponse(BaseModel):
    overall_attendance_pct: float
    total_conducted: int
    total_attended: int
    total_missed: int
    course_breakdown: List[Dict[str, Any]]
    attendance_trend: List[Dict[str, Any]]
    risk_analysis: AttendanceRiskSchema
    insufficient_data: bool


class StudentPerformanceAnalyticsResponse(BaseModel):
    assessment_average: Optional[float] = None
    total_assessments: int
    cgpa: float
    sgpa: float
    backlogs: int
    performance_by_course: List[Dict[str, Any]]
    performance_by_type: Dict[str, float]
    strongest_subjects: List[Dict[str, Any]]
    weakest_subjects: List[Dict[str, Any]]
    insufficient_data: bool


class StudentAnalyticsSummaryResponse(BaseModel):
    student_profile: Dict[str, Any]
    attendance_summary: StudentAttendanceAnalyticsResponse
    performance_summary: StudentPerformanceAnalyticsResponse
    risk_analysis: AttendanceRiskSchema
    recommendations: List[RecommendationSchema]
    insufficient_data: bool


class FacultyOfferingAnalyticsResponse(BaseModel):
    offering_id: str
    course_code: str
    course_title: str
    section: str
    total_enrolled: int
    average_attendance_pct: float
    average_assessment_pct: float
    students_requiring_attention: List[Dict[str, Any]]
    attendance_distribution: Dict[str, int]
    assessments: List[Dict[str, Any]]
    insufficient_data: bool


class AdminOverviewAnalyticsResponse(BaseModel):
    total_students: int
    total_faculty: int
    total_departments: int
    total_course_offerings: int
    average_cgpa: float
    average_attendance_pct: float
    students_below_attendance_threshold: int
    students_in_critical_risk: int
    students_with_backlogs: int


class AdminDepartmentAnalyticsResponse(BaseModel):
    department_id: str
    department_code: str
    department_name: str
    total_students: int
    total_faculty: int
    total_courses: int
    average_cgpa: float
    average_attendance_pct: float
    students_at_risk: int


class AdminProgramAnalyticsResponse(BaseModel):
    program_id: str
    program_code: str
    program_name: str
    duration_years: int
    total_students: int
    average_cgpa: float
    average_attendance_pct: float


# Phase 6 Governance, SSO, & System Enterprise Schemas
class SSOConfigSchema(BaseModel):
    id: str
    provider_name: str
    issuer_url: str
    client_id: str
    is_active: bool
    allow_jit_provisioning: bool
    created_at: str
    updated_at: str


class SSOLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider_id: str
    token_assertion: str
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    enrollment_no: Optional[str] = None



class AuditEventSchema(BaseModel):
    id: str
    event_type: str
    actor_username: str
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    details: Optional[str] = None
    timestamp: str


class AuditEventListResponse(BaseModel):
    total: int
    events: List[AuditEventSchema]


class RAGEvalMetricsSchema(BaseModel):
    context_precision: float
    context_recall: float
    faithfulness: float
    fallback_accuracy: float
    total_evaluated_queries: int
    evaluated_at: str


class SystemTaskSchema(BaseModel):
    id: str
    task_type: str
    status: str
    progress_pct: float
    details: Optional[str] = None
    initiated_by: str
    created_at: str
    updated_at: str


class DetailedSystemStatusResponse(BaseModel):
    status: str
    environment: str
    database: Dict[str, Any]
    vector_store: Dict[str, Any]
    active_sso_provider: Optional[str] = None
    rag_benchmark_latest: Optional[RAGEvalMetricsSchema] = None
    active_tasks: List[SystemTaskSchema]


class ReportExportResponse(BaseModel):
    report_type: str
    title: str
    generated_at: str
    generated_by: str
    checksum: str
    format: str
    content: str


# Phase 7 Interventions, Action Plans & Notification Schemas
class AcademicInterventionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    student_profile_id: str
    risk_category: str  # 'attendance', 'performance', 'backlog', 'general'
    title: str
    description: str
    recommended_action: str


class AcademicInterventionUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str  # 'pending', 'acknowledged', 'resolved'
    resolution_notes: Optional[str] = None


class AcademicInterventionResponse(BaseModel):
    id: str
    student_profile_id: str
    enrollment_no: str
    student_name: str
    issued_by_id: str
    issued_by_name: str
    risk_category: str
    title: str
    description: str
    recommended_action: str
    status: str
    resolution_notes: Optional[str] = None
    created_at: str
    updated_at: str


class AcademicInterventionListResponse(BaseModel):
    total: int
    interventions: List[AcademicInterventionResponse]


class StudentActionPlanCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    target_attendance_pct: Optional[float] = None
    target_sgpa: Optional[float] = None
    milestones: List[str]


class StudentActionPlanUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str  # 'active', 'completed', 'cancelled'
    milestones: Optional[List[str]] = None


class StudentActionPlanResponse(BaseModel):
    id: str
    student_profile_id: str
    enrollment_no: str
    title: str
    target_attendance_pct: Optional[float] = None
    target_sgpa: Optional[float] = None
    milestones: List[str]
    status: str
    created_at: str
    updated_at: str


class StudentActionPlanListResponse(BaseModel):
    total: int
    plans: List[StudentActionPlanResponse]


class NotificationAlertResponse(BaseModel):
    id: str
    user_id: str
    category: str
    severity: str
    title: str
    message: str
    is_read: bool
    link: Optional[str] = None
    created_at: str


class NotificationAlertListResponse(BaseModel):
    unread_count: int
    total: int
    notifications: List[NotificationAlertResponse]


class NotificationMarkReadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    notification_ids: List[str]
