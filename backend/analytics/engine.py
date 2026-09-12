"""
Core Academic Analytics Engine for CampusMIND 2.0.

Provides deterministic, auditable, and transparent statistical analytics
for Student, Faculty, and Admin scopes using normalized database entities.
"""
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from db.models import (
    StudentProfile,
    FacultyProfile,
    AttendanceRecord,
    Assessment,
    AssessmentGrade,
    Course,
    CourseOffering,
    Enrollment,
    Department,
    Program,
)
from analytics.risk_engine import attendance_risk_engine
from analytics.recommendation_engine import recommendation_engine


class AnalyticsEngine:
    """Core academic analytics execution engine."""

    # -------------------------------------------------------------------------
    # STUDENT ANALYTICS
    # -------------------------------------------------------------------------

    @classmethod
    def compute_student_attendance(
        cls, db: Session, student_profile_id: str, required_pct: float = 75.0
    ) -> Dict[str, Any]:
        """Calculates course-wise, overall, and trend attendance for a student."""
        records = (
            db.query(AttendanceRecord)
            .filter(AttendanceRecord.student_profile_id == student_profile_id)
            .order_by(AttendanceRecord.date.asc())
            .all()
        )

        if not records:
            # Fallback to student profile attendance_pct if records are empty
            sp = db.query(StudentProfile).filter(StudentProfile.id == student_profile_id).first()
            default_pct = sp.attendance_pct if sp else 0.0
            risk_res = attendance_risk_engine.calculate_risk(0, 0, required_pct)
            if sp:
                risk_res["attendance_percentage"] = default_pct

            return {
                "overall_attendance_pct": default_pct,
                "total_conducted": 0,
                "total_attended": 0,
                "total_missed": 0,
                "course_breakdown": [],
                "attendance_trend": [],
                "risk_analysis": risk_res,
                "insufficient_data": True if not sp else False,
            }

        total_conducted = len(records)
        total_attended = sum(1 for r in records if r.status in ("present", "late", "excused"))
        total_missed = total_conducted - total_attended
        overall_pct = round((total_attended / total_conducted) * 100.0, 2)

        # Course-wise breakdown
        course_map: Dict[str, Dict[str, Any]] = {}
        for r in records:
            c_key = r.course_id or (r.course_offering.course_id if r.course_offering else "general")
            c_title = "General Course"
            if r.course_offering and r.course_offering.course:
                c_title = r.course_offering.course.title
            elif r.course_id:
                c_obj = db.query(Course).filter(Course.id == r.course_id).first()
                if c_obj:
                    c_title = c_obj.title

            if c_key not in course_map:
                course_map[c_key] = {
                    "course_id": c_key,
                    "course_title": c_title,
                    "conducted": 0,
                    "attended": 0,
                    "missed": 0,
                }
            course_map[c_key]["conducted"] += 1
            if r.status in ("present", "late", "excused"):
                course_map[c_key]["attended"] += 1
            else:
                course_map[c_key]["missed"] += 1

        course_breakdown = []
        for c_data in course_map.values():
            cond = c_data["conducted"]
            att = c_data["attended"]
            pct = round((att / cond) * 100.0, 2) if cond > 0 else 100.0
            c_risk = attendance_risk_engine.calculate_risk(att, cond, required_pct)
            course_breakdown.append({
                "course_id": c_data["course_id"],
                "course_title": c_data["course_title"],
                "conducted": cond,
                "attended": att,
                "missed": c_data["missed"],
                "attendance_pct": pct,
                "risk_level": c_risk["risk_level"],
            })

        # Historical trend (cumulative percentage over time)
        trend = []
        running_conducted = 0
        running_attended = 0
        for r in records:
            running_conducted += 1
            if r.status in ("present", "late", "excused"):
                running_attended += 1
            trend.append({
                "date": r.date.strftime("%Y-%m-%d") if r.date else "",
                "cum_pct": round((running_attended / running_conducted) * 100.0, 2),
            })

        risk_analysis = attendance_risk_engine.calculate_risk(
            total_attended, total_conducted, required_pct
        )

        return {
            "overall_attendance_pct": overall_pct,
            "total_conducted": total_conducted,
            "total_attended": total_attended,
            "total_missed": total_missed,
            "course_breakdown": course_breakdown,
            "attendance_trend": trend[-20:],  # last 20 entries
            "risk_analysis": risk_analysis,
            "insufficient_data": False,
        }

    @classmethod
    def compute_student_performance(
        cls, db: Session, student_profile_id: str
    ) -> Dict[str, Any]:
        """Calculates assessment averages, course performance, and semester grades for a student."""
        grades = (
            db.query(AssessmentGrade)
            .join(Assessment)
            .filter(
                AssessmentGrade.student_profile_id == student_profile_id,
                Assessment.status == "published",
            )
            .all()
        )

        sp = db.query(StudentProfile).filter(StudentProfile.id == student_profile_id).first()

        if not grades:
            return {
                "assessment_average": None,
                "total_assessments": 0,
                "cgpa": sp.cgpa if sp else 0.0,
                "sgpa": sp.sgpa if sp else 0.0,
                "backlogs": sp.backlogs if sp else 0,
                "performance_by_course": [],
                "performance_by_type": {},
                "strongest_subjects": [],
                "weakest_subjects": [],
                "insufficient_data": True,
            }

        # Assessment performance by type & by course
        type_totals: Dict[str, List[float]] = {}
        course_totals: Dict[str, Dict[str, Any]] = {}
        pct_scores = []

        for g in grades:
            asm = g.assessment
            max_m = asm.max_marks if asm and asm.max_marks > 0 else 100.0
            pct_score = round((g.obtained_marks / max_m) * 100.0, 2)
            pct_scores.append(pct_score)

            a_type = asm.assessment_type if asm else "assignment"
            if a_type not in type_totals:
                type_totals[a_type] = []
            type_totals[a_type].append(pct_score)

            c_key = asm.course_id or (asm.course_offering.course_id if asm and asm.course_offering else "general")
            c_title = "General Course"
            if asm and asm.course_offering and asm.course_offering.course:
                c_title = asm.course_offering.course.title
            elif asm and asm.course_id:
                c_obj = db.query(Course).filter(Course.id == asm.course_id).first()
                if c_obj:
                    c_title = c_obj.title

            if c_key not in course_totals:
                course_totals[c_key] = {
                    "course_id": c_key,
                    "course_title": c_title,
                    "scores": [],
                }
            course_totals[c_key]["scores"].append(pct_score)

        avg_score = round(sum(pct_scores) / len(pct_scores), 2)

        perf_by_type = {
            atype: round(sum(scores) / len(scores), 2)
            for atype, scores in type_totals.items()
        }

        perf_by_course = []
        for c_data in course_totals.values():
            c_scores = c_data["scores"]
            c_avg = round(sum(c_scores) / len(c_scores), 2)
            perf_by_course.append({
                "course_id": c_data["course_id"],
                "course_title": c_data["course_title"],
                "score_pct": c_avg,
                "assessment_count": len(c_scores),
            })

        sorted_courses = sorted(perf_by_course, key=lambda x: x["score_pct"], reverse=True)
        strongest = sorted_courses[:2] if len(sorted_courses) >= 1 else []
        weakest = sorted(perf_by_course, key=lambda x: x["score_pct"])[:2] if len(sorted_courses) >= 1 else []

        return {
            "assessment_average": avg_score,
            "total_assessments": len(grades),
            "cgpa": sp.cgpa if sp else 0.0,
            "sgpa": sp.sgpa if sp else 0.0,
            "backlogs": sp.backlogs if sp else 0,
            "performance_by_course": perf_by_course,
            "performance_by_type": perf_by_type,
            "strongest_subjects": strongest,
            "weakest_subjects": weakest,
            "insufficient_data": False,
        }

    @classmethod
    def compute_student_summary(
        cls, db: Session, student_profile_id: str, required_pct: float = 75.0
    ) -> Dict[str, Any]:
        """Computes comprehensive student summary including risk & explainable recommendations."""
        sp = db.query(StudentProfile).filter(StudentProfile.id == student_profile_id).first()
        if not sp:
            return {"error": "Student profile not found", "insufficient_data": True}

        att_data = cls.compute_student_attendance(db, student_profile_id, required_pct)
        perf_data = cls.compute_student_performance(db, student_profile_id)

        sp_dict = {
            "id": sp.id,
            "user_id": sp.user_id,
            "enrollment_no": sp.enrollment_no,
            "branch": sp.branch,
            "year": sp.year,
            "semester": sp.semester,
            "cgpa": sp.cgpa,
            "sgpa": sp.sgpa,
            "attendance_pct": sp.attendance_pct,
            "backlogs": sp.backlogs,
        }

        recs = recommendation_engine.generate_student_recommendations(
            attendance_risk=att_data["risk_analysis"],
            performance_data=perf_data,
            student_profile=sp_dict,
        )

        return {
            "student_profile": sp_dict,
            "attendance_summary": att_data,
            "performance_summary": perf_data,
            "risk_analysis": att_data["risk_analysis"],
            "recommendations": recs,
            "insufficient_data": att_data["insufficient_data"] and perf_data["insufficient_data"],
        }

    # -------------------------------------------------------------------------
    # FACULTY ANALYTICS
    # -------------------------------------------------------------------------

    @classmethod
    def compute_faculty_offering_analytics(
        cls, db: Session, offering_id: str, faculty_profile_id: str
    ) -> Dict[str, Any]:
        """Calculates section-level attendance and assessment performance distribution for faculty."""
        offering = (
            db.query(CourseOffering)
            .filter(
                CourseOffering.id == offering_id,
                CourseOffering.faculty_profile_id == faculty_profile_id,
            )
            .first()
        )
        if not offering:
            return {"error": "Course offering not found or unauthorized", "unauthorized": True}

        enrollments = db.query(Enrollment).filter(Enrollment.course_offering_id == offering_id).all()
        enrolled_student_ids = [e.student_profile_id for e in enrollments]
        total_students = len(enrolled_student_ids)

        if total_students == 0:
            return {
                "offering_id": offering_id,
                "course_code": offering.course.code if offering.course else "",
                "course_title": offering.course.title if offering.course else "",
                "section": offering.section,
                "total_enrolled": 0,
                "average_attendance_pct": 0.0,
                "average_assessment_pct": 0.0,
                "students_requiring_attention": [],
                "attendance_distribution": {"safe": 0, "watch": 0, "at_risk": 0, "critical": 0},
                "assessments": [],
                "insufficient_data": True,
            }

        # Attendance calculation for students in this offering
        att_records = (
            db.query(AttendanceRecord)
            .filter(AttendanceRecord.course_offering_id == offering_id)
            .all()
        )

        student_att_counts: Dict[str, Dict[str, int]] = {}
        for r in att_records:
            sid = r.student_profile_id
            if sid not in student_att_counts:
                student_att_counts[sid] = {"conducted": 0, "attended": 0}
            student_att_counts[sid]["conducted"] += 1
            if r.status in ("present", "late", "excused"):
                student_att_counts[sid]["attended"] += 1

        dist = {"safe": 0, "watch": 0, "at_risk": 0, "critical": 0}
        students_attention = []
        att_pcts = []

        for sid in enrolled_student_ids:
            counts = student_att_counts.get(sid, {"conducted": 0, "attended": 0})
            c_cond = counts["conducted"]
            c_att = counts["attended"]
            sp = db.query(StudentProfile).filter(StudentProfile.id == sid).first()
            s_name = sp.user.display_name if sp and sp.user else "Student"
            s_enroll = sp.enrollment_no if sp else sid

            r_calc = attendance_risk_engine.calculate_risk(c_att, c_cond, 75.0)
            r_level = r_calc["risk_level"].lower()
            if r_level in dist:
                dist[r_level] += 1
            att_pcts.append(r_calc["attendance_percentage"])

            if r_calc["risk_level"] in ("AT_RISK", "CRITICAL"):
                students_attention.append({
                    "student_profile_id": sid,
                    "enrollment_no": s_enroll,
                    "student_name": s_name,
                    "reason": f"Attendance is {r_calc['attendance_percentage']}% ({r_calc['risk_level']})",
                    "attendance_pct": r_calc["attendance_percentage"],
                    "risk_level": r_calc["risk_level"],
                })

        avg_att = round(sum(att_pcts) / len(att_pcts), 2) if att_pcts else 0.0

        # Assessment performance in this offering
        assessments = db.query(Assessment).filter(Assessment.course_offering_id == offering_id).all()
        asm_summaries = []
        asm_avg_list = []

        for a in assessments:
            grades = db.query(AssessmentGrade).filter(AssessmentGrade.assessment_id == a.id).all()
            if grades:
                scores = [round((g.obtained_marks / a.max_marks) * 100.0, 2) for g in grades if a.max_marks > 0]
                a_avg = round(sum(scores) / len(scores), 2) if scores else 0.0
                asm_avg_list.append(a_avg)
            else:
                a_avg = 0.0

            asm_summaries.append({
                "assessment_id": a.id,
                "title": a.title,
                "type": a.assessment_type,
                "max_marks": a.max_marks,
                "average_pct": a_avg,
                "graded_count": len(grades),
            })

        overall_asm_avg = round(sum(asm_avg_list) / len(asm_avg_list), 2) if asm_avg_list else 0.0

        return {
            "offering_id": offering_id,
            "course_code": offering.course.code if offering.course else "",
            "course_title": offering.course.title if offering.course else "",
            "section": offering.section,
            "total_enrolled": total_students,
            "average_attendance_pct": avg_att,
            "average_assessment_pct": overall_asm_avg,
            "students_requiring_attention": students_attention,
            "attendance_distribution": dist,
            "assessments": asm_summaries,
            "insufficient_data": False,
        }

    # -------------------------------------------------------------------------
    # ADMIN ANALYTICS
    # -------------------------------------------------------------------------

    @classmethod
    def compute_admin_overview(cls, db: Session) -> Dict[str, Any]:
        """Calculates institution-wide aggregated academic stats."""
        total_students = db.query(func.count(StudentProfile.id)).scalar() or 0
        total_faculty = db.query(func.count(FacultyProfile.id)).scalar() or 0
        total_departments = db.query(func.count(Department.id)).scalar() or 0
        total_offerings = db.query(func.count(CourseOffering.id)).scalar() or 0

        avg_cgpa = db.query(func.avg(StudentProfile.cgpa)).scalar() or 0.0
        avg_att = db.query(func.avg(StudentProfile.attendance_pct)).scalar() or 0.0

        # Overall risk breakdown from student profiles
        at_risk_count = db.query(func.count(StudentProfile.id)).filter(StudentProfile.attendance_pct < 75.0).scalar() or 0
        critical_count = db.query(func.count(StudentProfile.id)).filter(StudentProfile.attendance_pct < 60.0).scalar() or 0
        backlog_students = db.query(func.count(StudentProfile.id)).filter(StudentProfile.backlogs > 0).scalar() or 0

        return {
            "total_students": total_students,
            "total_faculty": total_faculty,
            "total_departments": total_departments,
            "total_course_offerings": total_offerings,
            "average_cgpa": round(float(avg_cgpa), 2),
            "average_attendance_pct": round(float(avg_att), 2),
            "students_below_attendance_threshold": at_risk_count,
            "students_in_critical_risk": critical_count,
            "students_with_backlogs": backlog_students,
        }

    @classmethod
    def compute_admin_department_analytics(cls, db: Session, department_id: str) -> Dict[str, Any]:
        """Calculates department-level summary statistics."""
        dept = db.query(Department).filter(Department.id == department_id).first()
        if not dept:
            return {"error": "Department not found", "not_found": True}

        dept_students = db.query(StudentProfile).filter(StudentProfile.department_id == department_id).all()
        dept_faculty = db.query(FacultyProfile).filter(FacultyProfile.department_id == department_id).all()
        dept_courses = db.query(Course).filter(Course.department_id == department_id).all()

        total_s = len(dept_students)
        avg_cgpa = round(sum(s.cgpa for s in dept_students) / total_s, 2) if total_s > 0 else 0.0
        avg_att = round(sum(s.attendance_pct for s in dept_students) / total_s, 2) if total_s > 0 else 0.0
        at_risk = sum(1 for s in dept_students if s.attendance_pct < 75.0)

        return {
            "department_id": department_id,
            "department_code": dept.code,
            "department_name": dept.name,
            "total_students": total_s,
            "total_faculty": len(dept_faculty),
            "total_courses": len(dept_courses),
            "average_cgpa": avg_cgpa,
            "average_attendance_pct": avg_att,
            "students_at_risk": at_risk,
        }

    @classmethod
    def compute_admin_program_analytics(cls, db: Session, program_id: str) -> Dict[str, Any]:
        """Calculates program-level summary statistics."""
        prog = db.query(Program).filter(Program.id == program_id).first()
        if not prog:
            return {"error": "Program not found", "not_found": True}

        prog_students = db.query(StudentProfile).filter(StudentProfile.program_id == program_id).all()
        total_s = len(prog_students)
        avg_cgpa = round(sum(s.cgpa for s in prog_students) / total_s, 2) if total_s > 0 else 0.0
        avg_att = round(sum(s.attendance_pct for s in prog_students) / total_s, 2) if total_s > 0 else 0.0

        return {
            "program_id": program_id,
            "program_code": prog.code,
            "program_name": prog.name,
            "duration_years": prog.duration_years,
            "total_students": total_s,
            "average_cgpa": avg_cgpa,
            "average_attendance_pct": avg_att,
        }


analytics_engine = AnalyticsEngine()
