"""
Academic Audit & Institutional Intelligence Export Service for CampusMIND 2.0.
Generates deterministic text/CSV academic reports for students and administration with SHA-256 integrity verification.
"""
import hashlib
from datetime import datetime, timezone
from fastapi import HTTPException, status
from db.session import get_db_session
from models.schemas import ReportExportResponse, UserSchema
from services.analytics_service import analytics_service, AnalyticsService
from repositories.audit_repository import audit_repository, AuditRepository



class ExportService:
    """Service managing generation and export of academic audit reports."""

    def __init__(
        self,
        analytics_svc: AnalyticsService = analytics_service,
        audit_repo: AuditRepository = audit_repository,
    ):
        self.analytics_svc = analytics_svc
        self.audit_repo = audit_repo

    def export_student_report(self, user: UserSchema) -> ReportExportResponse:
        """Generates an official academic audit transcript export for the authenticated student."""
        if user.role != "student" or not user.enrollment_no:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Student export is restricted to authenticated student identity.",
            )

        with get_db_session() as db:
            summary = self.analytics_svc.get_student_me_summary(db, user)
        
        now_str = datetime.now(timezone.utc).isoformat()

        profile = summary.get("student_profile", {})
        att = summary.get("attendance_summary", {})
        perf = summary.get("performance_summary", {})
        risk = summary.get("risk_analysis", {})

        content_lines = [
            f"==========================================================================",
            f"CAMPUSMIND 2.0 — OFFICIAL STUDENT ACADEMIC AUDIT REPORT",
            f"==========================================================================",
            f"Generated At    : {now_str}",
            f"Student User    : {user.username}",
            f"Enrollment No   : {profile.get('enrollment_no', user.enrollment_no)}",
            f"Branch & Year   : {profile.get('branch', 'N/A')} (Year {profile.get('year', 'N/A')}, Sem {profile.get('semester', 'N/A')})",
            f"Cumulative GPA  : {perf.get('cgpa', 0.0)} / 10.0  (SGPA: {perf.get('sgpa', 0.0)})",
            f"Attendance Rate : {att.get('overall_attendance_pct', 0.0)}%",
            f"Backlog Count   : {perf.get('backlogs', 0)}",
            f"Fee Status      : {profile.get('fee_status', 'N/A')}",
            f"--------------------------------------------------------------------------",
            f"ATTENDANCE RISK ANALYSIS:",
            f"Risk Level      : {risk.get('risk_level', 'UNKNOWN')}",
            f"Attended/Total  : {risk.get('classes_attended', 0)} / {risk.get('classes_conducted', 0)} classes",
            f"Deficit Pct     : {risk.get('deficit_percentage', 0.0)}%",
            f"Recovery Rule   : {risk.get('explanation', '')}",
            f"--------------------------------------------------------------------------",
            f"RECOMMENDATIONS & GUIDANCE:",
        ]

        for idx, rec in enumerate(summary.get("recommendations", []), 1):
            severity = rec.get("severity", "info").upper() if isinstance(rec, dict) else getattr(rec, "severity", "info").upper()
            recommendation = rec.get("recommendation", "") if isinstance(rec, dict) else getattr(rec, "recommendation", "")
            reason = rec.get("reason", "") if isinstance(rec, dict) else getattr(rec, "reason", "")
            content_lines.append(f" {idx}. [{severity}] {recommendation}")
            content_lines.append(f"    Reason: {reason}")

        content_lines.append(f"==========================================================================")
        raw_text = "\n".join(content_lines)

        checksum = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

        self.audit_repo.log_audit_event(
            event_type="STUDENT_REPORT_EXPORTED",
            actor_username=user.username,
            details=f"Exported academic audit report for enrollment {user.enrollment_no} (Checksum {checksum[:12]})",
        )

        return ReportExportResponse(
            report_type="STUDENT_ACADEMIC_AUDIT",
            title=f"Academic_Audit_{user.enrollment_no}.txt",
            generated_at=now_str,
            generated_by=user.username,
            checksum=checksum,
            format="text/plain",
            content=raw_text,
        )

    def export_admin_report(self, user: UserSchema) -> ReportExportResponse:
        """Generates an institutional overview intelligence report for admin."""
        if user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin report export is restricted to Admin role.",
            )

        with get_db_session() as db:
            overview = self.analytics_svc.get_admin_overview(db, user)
        
        now_str = datetime.now(timezone.utc).isoformat()

        content_lines = [
            f"==========================================================================",
            f"CAMPUSMIND 2.0 — INSTITUTIONAL ACADEMIC OVERVIEW REPORT",
            f"==========================================================================",
            f"Generated At          : {now_str}",
            f"Administrator User    : {user.username}",
            f"Total Students        : {overview.get('total_students', 0)}",
            f"Total Faculty         : {overview.get('total_faculty', 0)}",
            f"Total Departments     : {overview.get('total_departments', 0)}",
            f"Total Course Offerings: {overview.get('total_course_offerings', 0)}",
            f"Institutional Avg CGPA: {overview.get('average_cgpa', 0.0)} / 10.0",
            f"Institutional Avg Att : {overview.get('average_attendance_pct', 0.0)}%",
            f"Students At Risk (<75%): {overview.get('students_below_attendance_threshold', 0)}",
            f"Students Critical (<60%): {overview.get('students_in_critical_risk', 0)}",
            f"Students With Backlogs: {overview.get('students_with_backlogs', 0)}",
            f"==========================================================================",
        ]
        raw_text = "\n".join(content_lines)
        checksum = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

        self.audit_repo.log_audit_event(
            event_type="ADMIN_REPORT_EXPORTED",
            actor_username=user.username,
            details=f"Exported institutional overview report (Checksum {checksum[:12]})",
        )

        return ReportExportResponse(
            report_type="INSTITUTIONAL_OVERVIEW",
            title="Institutional_Overview_Report.txt",
            generated_at=now_str,
            generated_by=user.username,
            checksum=checksum,
            format="text/plain",
            content=raw_text,
        )


export_service = ExportService()

