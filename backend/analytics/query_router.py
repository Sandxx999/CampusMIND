"""
Academic Analytics Query Intent Router for CampusMIND 2.0.

Extends basic query classification to route user queries intelligently
between institutional knowledge/RAG, student academic data, student analytics,
course analytics, faculty analytics, and admin analytics.
"""
import re
from typing import Dict, Any


class AcademicQueryRouter:
    """Intelligent intent router for academic chat queries."""

    INTENT_PATTERNS = {
        "STUDENT_ANALYTICS": [
            r"am\s+i\s+at\s+risk",
            r"why\s+am\s+i\s+at\s+risk",
            r"my\s+risk",
            r"attendance\s+risk",
            r"will\s+i\s+be\s+debarred",
            r"classes\s+needed",
            r"classes\s+i\s+need\s+to\s+attend",
            r"how\s+to\s+recover\s+attendance",
            r"recommendations?\s+for\s+me",
            r"how\s+can\s+i\s+improve",
            r"my\s+academic\s+risk",
            r"need\s+to\s+maintain",
        ],

        "STUDENT_ACADEMIC_DATA": [
            r"what\s+is\s+my\s+attendance",
            r"my\s+attendance\s+pct",
            r"my\s+attendance\s+percentage",
            r"my\s+sgpa",
            r"my\s+cgpa",
            r"my\s+grades",
            r"my\s+marks",
            r"my\s+backlogs",
            r"show\s+my\s+records?",
            r"my\s+overall\s+performance",
        ],
        "COURSE_ANALYTICS": [
            r"performance\s+in\s+([a-zA-Z0-9\s]+)",
            r"my\s+score\s+in\s+([a-zA-Z0-9\s]+)",
            r"how\s+is\s+my\s+performance\s+in",
            r"grade\s+in\s+([a-zA-Z0-9\s]+)",
            r"attendance\s+in\s+([a-zA-Z0-9\s]+)",
            r"course\s+performance",
        ],
        "FACULTY_ANALYTICS": [
            r"students?\s+in\s+my\s+section",
            r"students?\s+below\s+threshold",
            r"students?\s+at\s+risk",
            r"offering\s+performance",
            r"class\s+attendance\s+distribution",
            r"assessment\s+averages\s+for\s+my\s+course",
        ],
        "ADMIN_ANALYTICS": [
            r"department\s+statistics",
            r"program\s+statistics",
            r"institutional\s+overview",
            r"cse\s+department\s+attendance",
            r"department-level\s+summary",
            r"admin\s+analytics",
            r"attendance\s+statistics",
            r"department.*attendance",
            r"attendance.*department",
        ],

        "INSTITUTIONAL_KNOWLEDGE": [
            r"what\s+is\s+the\s+attendance\s+policy",
            r"attendance\s+rules?",
            r"minimum\s+attendance\s+required",
            r"grading\s+policy",
            r"passing\s+marks",
            r"curfew\s+time",
            r"fee\s+deadline",
        ],
    }

    @classmethod
    def classify_academic_query(cls, query: str) -> Dict[str, Any]:
        """
        Classifies query into precise academic analytics intent.

        Returns dict containing:
        - intent: category code
        - combined_policy_personal: bool (True if question asks policy + personal data, e.g. "What attendance do I need to maintain?")
        - course_target: extracted course name/code if any
        """
        query_lower = query.lower().strip()
        intent = "INSTITUTIONAL_KNOWLEDGE"
        combined = False
        course_target = None

        # Check combined query indicator: asking for policy + personal attendance
        if (
            ("attendance policy" in query_lower or "attendance rules" in query_lower or "how much attendance" in query_lower or "need to maintain" in query_lower)
            and ("my attendance" in query_lower or "do i" in query_lower or "am i" in query_lower or "my score" in query_lower or "my percentage" in query_lower)
        ):
            intent = "STUDENT_ANALYTICS"
            combined = True


        if not combined:
            for category, patterns in cls.INTENT_PATTERNS.items():
                for pat in patterns:
                    match = re.search(pat, query_lower)
                    if match:
                        intent = category
                        if category == "COURSE_ANALYTICS" and match.groups():
                            course_target = match.group(1).strip()
                        break
                if intent != "INSTITUTIONAL_KNOWLEDGE":
                    break

        return {
            "intent": intent,
            "combined_policy_personal": combined,
            "course_target": course_target,
        }


academic_query_router = AcademicQueryRouter()
