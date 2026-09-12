"""
Query Understanding & Normalization Engine for CampusMIND 2.0.

Provides query sanitization, prompt-injection defense stripping, and domain intent
classification ('institutional_knowledge', 'academic', 'events', 'policy', 'announcements',
'student_specific', 'faculty_specific', 'unsupported').
"""
import re
from typing import Dict, Any, List


class QueryProcessor:
    """Processes, normalizes, and classifies user queries prior to RAG retrieval."""

    INTENT_KEYWORDS = {
        "student_specific": [
            "my sgpa", "my cgpa", "my attendance", "my grades", "my backlogs",
            "my fee", "my transcript", "my timetable", "enrollment_no", "2024ifhe"
        ],
        "academic": [
            "course", "syllabus", "credit", "exam", "grade", "midterm", "endsem",
            "curriculum", "semester", "academic calendar", "department", "program"
        ],
        "policy": [
            "regulation", "rule", "guideline", "hostel curfew", "fee deadline",
            "penalty", "library rule", "conduct", "scholarship policy", "re-evaluation"
        ],
        "events": [
            "event", "workshop", "fest", "seminar", "auditorium", "timing",
            "organizer", "venue", "registration", "sports meet", "hackathon"
        ],
        "announcements": [
            "circular", "notice", "announcement", "news", "urgent", "update"
        ],
        "faculty_specific": [
            "grant", "research allocation", "teaching load", "faculty leave",
            "department budget", "appraisal"
        ],
    }

    @staticmethod
    def normalize_query(raw_query: str) -> str:
        """Sanitizes user input string and neutralizes potential prompt injection markers."""
        if not raw_query:
            return ""

        text = raw_query.strip()
        # Remove script tags or HTML tags
        text = re.sub(r"<[^>]*>", "", text)
        # Neutralize common prompt-injection phrasing
        text = re.sub(r"(?i)ignore\s+all\s+previous\s+instructions", "[sanitized]", text)
        text = re.sub(r"(?i)system\s+prompt", "[sanitized]", text)
        text = re.sub(r"(?i)reveal\s+secret", "[sanitized]", text)
        return text.strip()

    @classmethod
    def classify_intent(cls, query: str) -> str:
        """
        Classifies user query into institutional knowledge categories for retrieval optimization.
        Classification NEVER overrides server-side RBAC authorization.
        """
        query_lower = query.lower()

        # Check student specific intent
        if re.search(r"2024ifhe\d{3}", query_lower) or any(k in query_lower for k in cls.INTENT_KEYWORDS["student_specific"]):
            return "student_specific"

        for intent, keywords in cls.INTENT_KEYWORDS.items():
            if intent == "student_specific":
                continue
            if any(kw in query_lower for kw in keywords):
                return intent

        return "institutional_knowledge"

    @classmethod
    def process(cls, raw_query: str) -> Dict[str, Any]:
        """Runs full query pipeline returning normalized query and classification payload."""
        normalized = cls.normalize_query(raw_query)
        intent = cls.classify_intent(normalized)

        # Check for potential enrollment number in query
        match = re.search(r"2024IFHE\d{3}", normalized, re.IGNORECASE)
        enrollment_no = match.group(0).upper() if match else None

        return {
            "raw_query": raw_query,
            "normalized_query": normalized,
            "intent": intent,
            "target_enrollment_no": enrollment_no,
        }
