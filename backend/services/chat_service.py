"""
Chat & RAG Business Logic Service.
Handles rate limiting, vector retrieval, student record grounding, LLM generation,
and query feedback processing.
"""
import re
import time
import uuid
import warnings
from typing import Dict, List, Tuple

from fastapi import HTTPException, status
from auth.rbac import can_access_student_record
from core.config import settings
from core.logging import logger
from models.schemas import ChatRequest, ChatResponse, FeedbackRequest, SourceCitation, UserSchema
from rag.prompt_templates import rag_prompt
from repositories.audit_repository import audit_repository, AuditRepository
from repositories.student_repository import student_repository, StudentRepository

# Resilient Gemini SDK import
try:
    from google import genai
    LEGACY_GENAI = False
except ImportError:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import google.generativeai as genai
        LEGACY_GENAI = True
    except ImportError:
        genai = None
        LEGACY_GENAI = False


class ChatService:
    """Service managing RAG chat execution, rate limiting, and feedback."""

    def __init__(
        self,
        audit_repo: AuditRepository = audit_repository,
        student_repo: StudentRepository = student_repository,
    ):
        self.audit_repo = audit_repo
        self.student_repo = student_repo
        self.user_request_timestamps: Dict[str, List[float]] = {}

    def enforce_rate_limit(self, user: UserSchema) -> None:
        """Enforces per-user rate limiting using a sliding window strategy."""
        now = time.time()
        user_id = user.username
        timestamps = self.user_request_timestamps.get(user_id, [])
        valid_timestamps = [ts for ts in timestamps if now - ts < 60]

        if len(valid_timestamps) >= settings.RATE_LIMIT_PER_MINUTE:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded ({settings.RATE_LIMIT_PER_MINUTE} requests/min). Please try again shortly.",
            )

        valid_timestamps.append(now)
        self.user_request_timestamps[user_id] = valid_timestamps

    def synthesize_grounded_answer(self, query: str, retrieved_chunks: list) -> str:
        """Synthesizes structured Markdown answer grounded strictly in retrieved context."""
        if not retrieved_chunks:
            return "I don't have information on that in the official campus database."

        doc_snippets = {}
        for c in retrieved_chunks:
            doc_name = c.get("document_name", "Campus Document")
            snippet = c.get("snippet", "").strip()
            if doc_name not in doc_snippets:
                doc_snippets[doc_name] = []
            doc_snippets[doc_name].append(snippet)

        query_lower = query.lower()

        header_title = "Official Campus Information"
        if any(k in query_lower for k in ["grade", "cgpa", "sgpa", "transcript", "marksheet", "gpa", "score"]):
            header_title = "Official Grade Sheets & Transcripts Policy"
        elif any(k in query_lower for k in ["exam", "timetable", "schedule", "date", "mid-term", "end-sem", "test", "slot"]):
            header_title = "Semester Examination Schedule & Regulations"
        elif any(k in query_lower for k in ["hall ticket", "admit card", "entry pass", "hall-ticket"]):
            header_title = "Hall Ticket & Admit Card Rules"
        elif any(k in query_lower for k in ["certificate", "bonafide", "noc", "migration", "id card", "passport", "loan", "verification"]):
            header_title = "Student Certificates & Document Issuance Guidelines"
        elif any(k in query_lower for k in ["fee", "dues", "payment", "tuition", "scholarship", "fine"]):
            header_title = "Campus Fee Structure & Financial Policy"
        elif any(k in query_lower for k in ["placement", "job", "internship", "ppo", "cdc", "salary", "package"]):
            header_title = "Campus Placement & Internship Policy"
        elif any(k in query_lower for k in ["hostel", "mess", "curfew", "dining", "room", "food"]):
            header_title = "Hostel & Dining Regulations"

        response_lines = [f"### 📋 {header_title}\n"]

        seen_lines = set()
        key_points = []

        for doc_name, snippets in doc_snippets.items():
            for snippet in snippets:
                lines = snippet.split("\n")
                for line in lines:
                    line_str = line.strip()
                    if not line_str or line_str in seen_lines:
                        continue
                    if "IFHE HYDERABAD" in line_str or "FOUNDATION FOR HIGHER EDUCATION" in line_str:
                        continue

                    seen_lines.add(line_str)

                    if re.match(r"^\d+\.\s+", line_str):
                        key_points.append(f"\n**{line_str}**")
                    elif line_str.startswith("-") or line_str.startswith("*"):
                        key_points.append(f"  {line_str}")
                    else:
                        key_points.append(f"• {line_str}")

        if key_points:
            response_lines.append("\n".join(key_points))
        else:
            for doc_name, snippets in doc_snippets.items():
                response_lines.append(f"\n**Source:** `{doc_name}`\n" + "\n".join(snippets))

        cited_docs = ", ".join([f"`{name}`" for name in doc_snippets.keys()])
        response_lines.append(f"\n\n---\n*Information verified against official campus records: {cited_docs}*")

        return "\n".join(response_lines)

    def generate_llm_answer(self, prompt_text: str, retrieved_chunks: list = None, question: str = "") -> str:
        """Invokes Gemini API or falls back to grounded synthesis."""
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "dummy_key_replace_with_real":
            try:
                if LEGACY_GENAI and genai:
                    genai.configure(api_key=settings.GEMINI_API_KEY)
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    response = model.generate_content(prompt_text)
                    if response and response.text:
                        return response.text
                elif genai:
                    client = genai.Client(api_key=settings.GEMINI_API_KEY)
                    response = client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=prompt_text,
                    )
                    if response and response.text:
                        return response.text
            except Exception as e:
                logger.error(f"Error calling Gemini API: {e}")

        return self.synthesize_grounded_answer(question, retrieved_chunks)

    def process_chat_query(self, request: ChatRequest, user: UserSchema) -> ChatResponse:
        """Processes user chat request using vector retrieval, DB grounding, and LLM synthesis."""
        self.enforce_rate_limit(user)
        start_time = time.time()
        query_id = f"qry_{uuid.uuid4().hex[:8]}"

        clean_message = request.message.strip().replace("<script>", "").replace("</script>", "")

        # Deferred vector retrieval import
        from rag.retriever import retriever_instance

        retrieved_chunks, max_confidence = retriever_instance.retrieve_chunks(
            query=clean_message, user_role=user.role
        )

        # Grounding with student record if authorized
        match = re.search(r"2024IFHE\d{3}", clean_message, re.IGNORECASE)
        if match and can_access_student_record(user, match.group(0)):
            enrollment_no = match.group(0).upper()
            try:
                student_row = self.student_repo.get_by_enrollment(enrollment_no)
                if student_row:
                    s = student_row
                    student_snippet = (
                        f"DEMO / SYNTHETIC STUDENT RECORD: {s['enrollment_no']}\n"
                        f"• Name: {s['name']}\n"
                        f"• Enrollment No: {s['enrollment_no']}\n"
                        f"• Email: {s['email']}\n"
                        f"• Mobile Number: {s['mobile_no']}\n"
                        f"• Branch / Department: {s['branch']}\n"
                        f"• Academic Year: Year {s['year']} (Semester {s['semester']})\n"
                        f"• Enrolled Courses: {s['courses_enrolled']}\n"
                        f"• Current Semester SGPA: {s['sgpa']}\n"
                        f"• Cumulative CGPA: {s['cgpa']}\n"
                        f"• Attendance Percentage: {s['attendance_pct']}%\n"
                        f"• Active Backlogs: {s['backlogs']}\n"
                        f"• Tuition Fee Status: {s['fee_status']}"
                    )
                    retrieved_chunks.insert(
                        0,
                        {
                            "document_name": "ifhe_student_directory_records.txt",
                            "snippet": student_snippet,
                            "score": 0.99,
                        },
                    )
                    max_confidence = max(max_confidence, 0.99)
            except Exception as e:
                logger.error(f"Error querying student repository during RAG chat: {e}")

        # Check threshold
        if not retrieved_chunks or max_confidence < settings.SIMILARITY_THRESHOLD:
            fallback_answer = "I don't have information on that in the official campus database."
            latency_ms = round((time.time() - start_time) * 1000, 2)

            self.audit_repo.log_query(
                query_id=query_id,
                username=user.username,
                role=user.role,
                question=clean_message,
                answer=fallback_answer,
                latency_ms=latency_ms,
                chunk_count=0,
                confidence=max_confidence,
                is_fallback=True,
            )

            return ChatResponse(
                query_id=query_id,
                answer=fallback_answer,
                sources=[],
                confidence=max_confidence,
                is_fallback=True,
            )

        formatted_context = "\n\n".join([f"[{c['document_name']}]: {c['snippet']}" for c in retrieved_chunks])
        prompt_text = rag_prompt.format(context=formatted_context, question=clean_message)

        answer_text = self.generate_llm_answer(prompt_text, retrieved_chunks=retrieved_chunks, question=clean_message)
        latency_ms = round((time.time() - start_time) * 1000, 2)

        sources = [
            SourceCitation(
                document_name=c["document_name"],
                snippet=c["snippet"][:200] + ("..." if len(c["snippet"]) > 200 else ""),
                score=c["score"],
            )
            for c in retrieved_chunks
        ]

        self.audit_repo.log_query(
            query_id=query_id,
            username=user.username,
            role=user.role,
            question=clean_message,
            answer=answer_text,
            latency_ms=latency_ms,
            chunk_count=len(retrieved_chunks),
            confidence=max_confidence,
            is_fallback=False,
        )

        return ChatResponse(
            query_id=query_id,
            answer=answer_text,
            sources=sources,
            confidence=max_confidence,
            is_fallback=False,
        )

    def submit_feedback(self, request: FeedbackRequest, user: UserSchema) -> dict:
        """Processes user feedback submission, ensuring ownership of the query."""
        owner = self.audit_repo.get_query_owner(request.query_id)
        if owner is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The referenced query was not found.",
            )
        if owner != user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You may only submit feedback for your own queries.",
            )
        self.audit_repo.log_feedback(request.query_id, request.is_positive)
        return {"status": "success", "message": "Feedback recorded successfully."}


chat_service = ChatService()
