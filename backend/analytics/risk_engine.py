"""
Attendance Risk Analysis Engine for CampusMIND 2.0.

Provides deterministic, explainable attendance risk classification,
deficit calculations, and mathematical recovery estimates based on actual database records.
"""
import math
from typing import Dict, Any, Optional


class AttendanceRiskEngine:
    """Deterministic attendance risk analysis engine."""

    DEFAULT_REQUIRED_PCT: float = 75.0

    @classmethod
    def calculate_risk(
        cls,
        attended_classes: int,
        conducted_classes: int,
        required_pct: float = DEFAULT_REQUIRED_PCT,
    ) -> Dict[str, Any]:
        """
        Calculates attendance risk, deficit, recovery requirement, and explanation.

        Risk levels:
        - SAFE: percentage >= required_pct
        - WATCH: percentage >= required_pct - 5.0 (e.g., 70% to 74.9%)
        - AT_RISK: percentage >= required_pct - 15.0 (e.g., 60% to 69.9%)
        - CRITICAL: percentage < required_pct - 15.0 (e.g., < 60%)
        """
        if conducted_classes <= 0:
            return {
                "risk_level": "UNKNOWN",
                "attendance_percentage": 0.0,
                "required_percentage": required_pct,
                "classes_attended": 0,
                "classes_conducted": 0,
                "classes_missed": 0,
                "deficit_percentage": 0.0,
                "classes_needed_to_recover": 0,
                "is_recoverable": True,
                "insufficient_data": True,
                "explanation": "Insufficient attendance record data conducted to compute risk status.",
            }

        attended_classes = max(0, min(attended_classes, conducted_classes))
        missed_classes = conducted_classes - attended_classes
        current_pct = round((attended_classes / conducted_classes) * 100.0, 2)

        if current_pct >= required_pct:
            risk_level = "SAFE"
            deficit_pct = 0.0
            classes_needed = 0
            is_recoverable = True
            explanation = (
                f"Attendance ({current_pct}%) meets or exceeds the required institutional "
                f"threshold of {required_pct}% ({attended_classes}/{conducted_classes} classes attended)."
            )
        else:
            deficit_pct = round(required_pct - current_pct, 2)
            req_ratio = required_pct / 100.0

            if req_ratio >= 1.0:
                is_recoverable = False
                classes_needed = 0
                explanation = "Required threshold is 100%, recovery is not possible after missing classes."
            else:
                # Formula: (req_ratio * conducted - attended) / (1 - req_ratio)
                numerator = req_ratio * conducted_classes - attended_classes
                denominator = 1.0 - req_ratio
                raw_needed = math.ceil(numerator / denominator)
                classes_needed = max(0, raw_needed)
                is_recoverable = True

            if current_pct >= (required_pct - 5.0):
                risk_level = "WATCH"
                explanation = (
                    f"Attendance ({current_pct}%) is slightly below the required threshold of {required_pct}% "
                    f"with a deficit of {deficit_pct}%. Attending the next {classes_needed} consecutive class(es) "
                    f"will restore attendance to {required_pct}%."
                )
            elif current_pct >= (required_pct - 15.0):
                risk_level = "AT_RISK"
                explanation = (
                    f"Attendance ({current_pct}%) is at risk below the required threshold of {required_pct}% "
                    f"with a deficit of {deficit_pct}%. You must attend the next {classes_needed} consecutive "
                    f"class(es) without missing to recover policy compliance."
                )
            else:
                risk_level = "CRITICAL"
                explanation = (
                    f"Attendance ({current_pct}%) is critically low below the required threshold of {required_pct}% "
                    f"with a deficit of {deficit_pct}%. Attending the next {classes_needed} consecutive class(es) "
                    f"is required to achieve the minimum {required_pct}% threshold."
                )

        return {
            "risk_level": risk_level,
            "attendance_percentage": current_pct,
            "required_percentage": required_pct,
            "classes_attended": attended_classes,
            "classes_conducted": conducted_classes,
            "classes_missed": missed_classes,
            "deficit_percentage": deficit_pct,
            "classes_needed_to_recover": classes_needed,
            "is_recoverable": is_recoverable,
            "insufficient_data": False,
            "explanation": explanation,
        }


attendance_risk_engine = AttendanceRiskEngine()
