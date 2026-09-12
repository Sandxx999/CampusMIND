"""
Explainable Recommendation Engine for CampusMIND 2.0.

Generates rule-based, deterministic academic recommendations grounded
strictly in actual student performance metrics and attendance data.
"""
from typing import List, Dict, Any, Optional


class RecommendationEngine:
    """Deterministic recommendation generator based on actual student metrics."""

    @classmethod
    def generate_student_recommendations(
        cls,
        attendance_risk: Dict[str, Any],
        performance_data: Dict[str, Any],
        student_profile: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Generates grounded academic recommendations for a student.

        Returns list of recommendation objects containing:
        - recommendation: actionable text statement
        - reason: explanation based on actual metrics
        - supporting_metrics: key metrics backing the recommendation
        - severity: 'critical' | 'warning' | 'info' | 'positive'
        - source: 'attendance_records' | 'assessment_grades' | 'system_policy' | 'student_profile'
        """
        recommendations: List[Dict[str, Any]] = []

        # Rule 1: Attendance Risk Guidance
        if attendance_risk.get("insufficient_data"):
            recommendations.append({
                "recommendation": "Await Initial Attendance Records",
                "reason": "Attendance data for the current academic term is not yet populated.",
                "supporting_metrics": {"classes_conducted": 0},
                "severity": "info",
                "source": "attendance_records",
            })
        else:
            risk_level = attendance_risk.get("risk_level")
            needed = attendance_risk.get("classes_needed_to_recover", 0)
            att_pct = attendance_risk.get("attendance_percentage", 100.0)
            req_pct = attendance_risk.get("required_percentage", 75.0)

            if risk_level in ("CRITICAL", "AT_RISK"):
                recommendations.append({
                    "recommendation": f"Attend Next {needed} Consecutive Classes to Restore Eligibility",
                    "reason": f"Current attendance ({att_pct}%) is below institutional threshold ({req_pct}%).",
                    "supporting_metrics": {
                        "current_attendance_pct": att_pct,
                        "required_pct": req_pct,
                        "classes_needed": needed,
                    },
                    "severity": "critical" if risk_level == "CRITICAL" else "warning",
                    "source": "attendance_records",
                })
            elif risk_level == "WATCH":
                recommendations.append({
                    "recommendation": f"Maintain Regular Attendance to Overcome Margin ({att_pct}%)",
                    "reason": f"Attendance is near the threshold of {req_pct}%. Missing classes may trigger academic risk.",
                    "supporting_metrics": {
                        "current_attendance_pct": att_pct,
                        "deficit_pct": attendance_risk.get("deficit_percentage", 0.0),
                    },
                    "severity": "warning",
                    "source": "attendance_records",
                })
            elif risk_level == "SAFE" and att_pct >= 85.0:
                recommendations.append({
                    "recommendation": "Sustain Excellent Attendance Pace",
                    "reason": f"Strong attendance record of {att_pct}% ensures full eligibility for end-term examinations.",
                    "supporting_metrics": {"current_attendance_pct": att_pct},
                    "severity": "positive",
                    "source": "attendance_records",
                })

        # Rule 2: Assessment Performance Guidance
        assessment_avg = performance_data.get("assessment_average")
        weakest_subjects = performance_data.get("weakest_subjects", [])
        strongest_subjects = performance_data.get("strongest_subjects", [])
        total_assessments = performance_data.get("total_assessments", 0)

        if total_assessments == 0 or assessment_avg is None:
            recommendations.append({
                "recommendation": "Complete Upcoming Course Assessments",
                "reason": "No evaluation marks recorded yet for the active semester.",
                "supporting_metrics": {"total_assessments_recorded": 0},
                "severity": "info",
                "source": "assessment_grades",
            })
        else:
            if assessment_avg < 50.0:
                recommendations.append({
                    "recommendation": "Schedule Office Hours Consultation with Course Instructors",
                    "reason": f"Overall assessment average ({assessment_avg}%) indicates academic difficulty.",
                    "supporting_metrics": {"assessment_average_pct": assessment_avg},
                    "severity": "critical",
                    "source": "assessment_grades",
                })
            elif assessment_avg < 70.0:
                recommendations.append({
                    "recommendation": "Focus Revision on Core Assessment Topics",
                    "reason": f"Current assessment average stands at {assessment_avg}%. Dedicated review will improve semester scores.",
                    "supporting_metrics": {"assessment_average_pct": assessment_avg},
                    "severity": "warning",
                    "source": "assessment_grades",
                })
            elif assessment_avg >= 80.0:
                recommendations.append({
                    "recommendation": "Maintain Current Study Strategy for Upcoming Midterm/Final Exams",
                    "reason": f"High assessment performance of {assessment_avg}% demonstrates effective understanding of course concepts.",
                    "supporting_metrics": {"assessment_average_pct": assessment_avg},
                    "severity": "positive",
                    "source": "assessment_grades",
                })

            if weakest_subjects:
                weak_course = weakest_subjects[0]
                course_name = weak_course.get("course_title", weak_course.get("course_code", "Course"))
                score = weak_course.get("score_pct", 0.0)
                if score < 60.0:
                    recommendations.append({
                        "recommendation": f"Prioritize Practice and Remedial Material for {course_name}",
                        "reason": f"Subject performance in {course_name} is currently lower ({score}%) than peer average.",
                        "supporting_metrics": {
                            "course": course_name,
                            "course_score_pct": score,
                        },
                        "severity": "warning",
                        "source": "assessment_grades",
                    })

        # Rule 3: Backlog / CGPA Guidance
        backlogs = student_profile.get("backlogs", 0)
        cgpa = student_profile.get("cgpa", 0.0)
        if backlogs > 0:
            recommendations.append({
                "recommendation": f"Register for Supplementary / Re-examination Clearing ({backlogs} Active Backlog(s))",
                "reason": f"Student profile indicates {backlogs} unresolved backlog course(s).",
                "supporting_metrics": {"active_backlogs": backlogs, "cgpa": cgpa},
                "severity": "critical",
                "source": "student_profile",
            })

        if not recommendations:
            recommendations.append({
                "recommendation": "Maintain Consistent Academic Progress",
                "reason": "Current metrics align with academic standards.",
                "supporting_metrics": {"cgpa": cgpa},
                "severity": "info",
                "source": "system_policy",
            })

        return recommendations


recommendation_engine = RecommendationEngine()
