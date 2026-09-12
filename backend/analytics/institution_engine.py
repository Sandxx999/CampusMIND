import os
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from db.models import (
    StudentProfile, Department, Course, AttendanceRecord,
    AssessmentGrade, Assessment, AcademicIntervention, StudentActionPlan, Enrollment
)
from fastapi import HTTPException

MIN_POPULATION = int(os.getenv("ANALYTICS_MIN_POPULATION", "5"))

class InstitutionEngine:
    def _check_privacy(self, count: int):
        if count > 0 and count < MIN_POPULATION:
            raise HTTPException(status_code=400, detail="Insufficient population size for privacy-preserving aggregation.")

    def compute_overview(self, db: Session, academic_year: str = None, semester: int = None) -> Dict[str, Any]:
        query = db.query(StudentProfile)
        if semester is not None:
            query = query.filter(StudentProfile.semester == semester)

        total_students = query.count()
        if total_students == 0:
            return {
                "total_students": 0,
                "average_cgpa": 0.0,
                "average_attendance_pct": 0.0,
                "students_at_risk": 0,
                "students_critical": 0
            }

        self._check_privacy(total_students)

        avg_cgpa = db.query(func.avg(StudentProfile.cgpa)).scalar() or 0.0
        avg_att = db.query(func.avg(StudentProfile.attendance_pct)).scalar() or 0.0
        at_risk = db.query(func.count(StudentProfile.id)).filter(StudentProfile.attendance_pct < 75.0).scalar() or 0
        critical = db.query(func.count(StudentProfile.id)).filter(StudentProfile.attendance_pct < 60.0).scalar() or 0

        return {
            "total_students": total_students,
            "average_cgpa": round(float(avg_cgpa), 2),
            "average_attendance_pct": round(float(avg_att), 2),
            "students_at_risk": at_risk,
            "students_critical": critical
        }

    def compute_attendance_trends(self, db: Session, department_id: str = None, academic_year: str = None) -> List[Dict[str, Any]]:
        query = db.query(
            Department.name,
            func.avg(StudentProfile.attendance_pct).label('avg_att'),
            func.count(StudentProfile.id).label('student_count')
        ).join(StudentProfile, Department.id == StudentProfile.department_id)

        if department_id:
            query = query.filter(Department.id == department_id)

        query = query.group_by(Department.name)
        results = query.all()

        trends = []
        for r in results:
            if r.student_count < MIN_POPULATION:
                continue
            trends.append({
                "department": r.name,
                "average_attendance_pct": round(float(r.avg_att), 2),
                "population": r.student_count
            })
        return trends

    def compute_performance_trends(self, db: Session, department_id: str = None, academic_year: str = None) -> List[Dict[str, Any]]:
        query = db.query(
            Department.name,
            func.avg(StudentProfile.cgpa).label('avg_cgpa'),
            func.count(StudentProfile.id).label('student_count')
        ).join(StudentProfile, Department.id == StudentProfile.department_id)

        if department_id:
            query = query.filter(Department.id == department_id)

        query = query.group_by(Department.name)
        results = query.all()

        trends = []
        for r in results:
            if r.student_count < MIN_POPULATION:
                continue
            trends.append({
                "department": r.name,
                "average_cgpa": round(float(r.avg_cgpa), 2),
                "population": r.student_count
            })
        return trends

    def compute_risk_summary(self, db: Session, department_id: str = None) -> Dict[str, Any]:
        query = db.query(StudentProfile)
        if department_id:
            query = query.filter(StudentProfile.department_id == department_id)

        total = query.count()
        if total == 0:
            return {
                "total_students": 0,
                "at_risk_count": 0,
                "critical_risk_count": 0,
                "backlog_count": 0
            }

        self._check_privacy(total)

        at_risk = query.filter(StudentProfile.attendance_pct < 75.0).count()
        critical = query.filter(StudentProfile.attendance_pct < 60.0).count()
        backlogs = query.filter(StudentProfile.backlogs > 0).count()

        return {
            "total_students": total,
            "at_risk_count": at_risk,
            "critical_risk_count": critical,
            "backlog_count": backlogs
        }

    def compute_interventions_summary(self, db: Session, department_id: str = None) -> Dict[str, Any]:
        q_inv = db.query(AcademicIntervention).join(StudentProfile)
        if department_id:
            q_inv = q_inv.filter(StudentProfile.department_id == department_id)

        total_inv = q_inv.count()
        pending_inv = q_inv.filter(AcademicIntervention.status == 'pending').count()
        resolved_inv = q_inv.filter(AcademicIntervention.status == 'resolved').count()

        q_plans = db.query(StudentActionPlan).join(StudentProfile)
        if department_id:
            q_plans = q_plans.filter(StudentProfile.department_id == department_id)

        total_plans = q_plans.count()
        completed_plans = q_plans.filter(StudentActionPlan.status == 'completed').count()

        return {
            "total_interventions": total_inv,
            "pending_interventions": pending_inv,
            "resolved_interventions": resolved_inv,
            "total_action_plans": total_plans,
            "completed_action_plans": completed_plans,
            "intervention_resolution_rate": round(resolved_inv / total_inv * 100, 2) if total_inv > 0 else 0.0,
            "plan_completion_rate": round(completed_plans / total_plans * 100, 2) if total_plans > 0 else 0.0
        }

    def compute_department_performance(self, db: Session) -> List[Dict[str, Any]]:
        return self.compute_performance_trends(db)

    def compute_decision_support(self, db: Session, department_id: str = None) -> Dict[str, Any]:
        risk_summary = self.compute_risk_summary(db, department_id)
        interventions_summary = self.compute_interventions_summary(db, department_id)

        signals = []
        recommendations = []

        total = risk_summary.get("total_students", 0)
        if total >= MIN_POPULATION:
            critical = risk_summary.get("critical_risk_count", 0)
            critical_pct = (critical / total) * 100
            if critical_pct > 15:
                signals.append({
                    "indicator": "Elevated Critical Risk",
                    "value": critical_pct,
                    "severity": "high",
                    "explanation": f"{critical_pct:.1f}% of students have < 60% attendance."
                })
                recommendations.append({
                    "category": "Intervention",
                    "recommendation": "Initiate department-wide attendance recovery meetings.",
                    "priority": "high"
                })
            elif critical_pct > 5:
                signals.append({
                    "indicator": "Moderate Critical Risk",
                    "value": critical_pct,
                    "severity": "medium",
                    "explanation": f"{critical_pct:.1f}% of students have < 60% attendance."
                })

            total_inv = interventions_summary.get("total_interventions", 0)
            pending_inv = interventions_summary.get("pending_interventions", 0)
            if total_inv > 0:
                pending_pct = (pending_inv / total_inv) * 100
                if pending_pct > 50:
                    signals.append({
                        "indicator": "Intervention Backlog",
                        "value": pending_pct,
                        "severity": "high",
                        "explanation": f"{pending_pct:.1f}% of interventions are unresolved."
                    })
                    recommendations.append({
                        "category": "Workload",
                        "recommendation": "Assign additional faculty advisors to resolve pending interventions.",
                        "priority": "high"
                    })

            plan_completion = interventions_summary.get("plan_completion_rate", 0)
            if interventions_summary.get("total_action_plans", 0) > 0 and plan_completion < 40:
                signals.append({
                    "indicator": "Low Plan Completion",
                    "value": plan_completion,
                    "severity": "medium",
                    "explanation": f"Only {plan_completion:.1f}% of action plans are completed."
                })
                recommendations.append({
                    "category": "Monitoring",
                    "recommendation": "Review effectiveness of current action plan templates.",
                    "priority": "medium"
                })

        return {
            "risk_signals": signals,
            "recommendations": recommendations
        }

institution_engine = InstitutionEngine()
