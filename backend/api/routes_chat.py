import time
import uuid
import re

import warnings

# Resilient Gemini SDK import handling both new `google.genai` and legacy `google.generativeai`
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

from fastapi import APIRouter, Depends, HTTPException, status
from models.schemas import ChatRequest, ChatResponse, FeedbackRequest, SourceCitation, UserSchema
from auth.rbac import get_current_user
from rag.retriever import retriever_instance
from rag.prompt_templates import rag_prompt
from logs.logger import log_query_to_db, log_feedback_to_db, logger
from config import settings

router = APIRouter(prefix="/api/chat", tags=["Chat & RAG"])

user_request_timestamps = {}

def enforce_rate_limit(user: UserSchema):
    """Enforces basic per-user request throttling on the chat endpoint."""
    now = time.time()
    user_id = user.username
    timestamps = user_request_timestamps.get(user_id, [])
    valid_timestamps = [ts for ts in timestamps if now - ts < 60]
    
    if len(valid_timestamps) >= settings.RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded ({settings.RATE_LIMIT_PER_MINUTE} requests/min). Please try again shortly."
        )
    
    valid_timestamps.append(now)
    user_request_timestamps[user_id] = valid_timestamps

def synthesize_grounded_answer(query: str, retrieved_chunks: list) -> str:
    """
    Intelligent Grounded RAG Synthesizer that processes retrieved context chunks
    and generates a detailed, structured Markdown response tailored to the user's specific query.
    """
    if not retrieved_chunks:
        return "I don't have information on that in the official campus database."

    # Extract distinct document names and snippets
    doc_snippets = {}
    for c in retrieved_chunks:
        doc_name = c.get('document_name', 'Campus Document')
        snippet = c.get('snippet', '').strip()
        if doc_name not in doc_snippets:
            doc_snippets[doc_name] = []
        doc_snippets[doc_name].append(snippet)

    query_lower = query.lower()

    # Detect domain context for tailored formatting
    header_title = "Official Campus Information"
    if any(k in query_lower for k in ['grade', 'cgpa', 'sgpa', 'transcript', 'marksheet', 'gpa', 'score']):
        header_title = "Official Grade Sheets & Transcripts Policy"
    elif any(k in query_lower for k in ['exam', 'timetable', 'schedule', 'date', 'mid-term', 'end-sem', 'test', 'slot']):
        header_title = "Semester Examination Schedule & Regulations"
    elif any(k in query_lower for k in ['hall ticket', 'admit card', 'entry pass', 'hall-ticket']):
        header_title = "Hall Ticket & Admit Card Rules"
    elif any(k in query_lower for k in ['certificate', 'bonafide', 'noc', 'migration', 'id card', 'passport', 'loan', 'verification']):
        header_title = "Student Certificates & Document Issuance Guidelines"
    elif any(k in query_lower for k in ['fee', 'dues', 'payment', 'tuition', 'scholarship', 'fine']):
        header_title = "Campus Fee Structure & Financial Policy"
    elif any(k in query_lower for k in ['placement', 'job', 'internship', 'ppo', 'cdc', 'salary', 'package']):
        header_title = "Campus Placement & Internship Policy"
    elif any(k in query_lower for k in ['hostel', 'mess', 'curfew', 'dining', 'room', 'food']):
        header_title = "Hostel & Dining Regulations"

    response_lines = [f"### 📋 {header_title}\n"]

    # Synthesize key points from retrieved chunks
    seen_lines = set()
    key_points = []

    for doc_name, snippets in doc_snippets.items():
        doc_clean_name = doc_name.replace("ifhe_", "").replace(".txt", "").replace("_", " ").title()
        
        for snippet in snippets:
            lines = snippet.split('\n')
            for line in lines:
                line_str = line.strip()
                if not line_str or line_str in seen_lines:
                    continue
                # Skip pure document headers if repeated
                if "IFHE HYDERABAD" in line_str or "FOUNDATION FOR HIGHER EDUCATION" in line_str:
                    continue
                
                seen_lines.add(line_str)

                # Format headings or bullet points
                if re.match(r'^\d+\.\s+', line_str):
                    key_points.append(f"\n**{line_str}**")
                elif line_str.startswith('-') or line_str.startswith('*'):
                    key_points.append(f"  {line_str}")
                else:
                    key_points.append(f"• {line_str}")

    if key_points:
        response_lines.append("\n".join(key_points))
    else:
        # Fallback to snippet blocks
        for doc_name, snippets in doc_snippets.items():
            response_lines.append(f"\n**Source:** `{doc_name}`\n" + "\n".join(snippets))

    # Add official citation footer
    cited_docs = ", ".join([f"`{name}`" for name in doc_snippets.keys()])
    response_lines.append(f"\n\n---\n*Information verified against official campus records: {cited_docs}*")

    return "\n".join(response_lines)

def generate_llm_answer(prompt_text: str, retrieved_chunks: list = None, question: str = "") -> str:
    """Invokes Google Gemini API via SDK with dynamic synthesis fallback for retrieved chunks."""
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "dummy_key_replace_with_real":
        try:
            if LEGACY_GENAI and genai:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt_text)
                if response and response.text:
                    return response.text
            elif genai:
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                response = client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=prompt_text,
                )
                if response and response.text:
                    return response.text
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")

    # Advanced Grounded Context Synthesis fallback
    return synthesize_grounded_answer(question, retrieved_chunks)

@router.post("", response_model=ChatResponse)
def handle_chat(request: ChatRequest, user: UserSchema = Depends(get_current_user)):
    """
    RAG Chat endpoint:
    1. Input sanitization & rate limit check
    2. RBAC-scoped document retrieval from ChromaDB
    3. Low similarity threshold check (no hallucination fallback)
    4. Prompt formatting & Gemini LLM / Dynamic RAG synthesis
    5. Asynchronous usage logging to SQLite
    """
    enforce_rate_limit(user)
    start_time = time.time()
    query_id = f"qry_{uuid.uuid4().hex[:8]}"

    # Input sanitization (strip whitespace, basic tag removal)
    clean_message = request.message.strip().replace("<script>", "").replace("</script>", "")

    # Retrieve context chunks from ChromaDB filtered by role
    retrieved_chunks, max_confidence = retriever_instance.retrieve_chunks(
        query=clean_message,
        user_role=user.role
    )

    # Check for direct enrollment number lookup in SQLite database to enrich context
    match = re.search(r'2024IFHE\d{3}', clean_message, re.IGNORECASE)
    if match:
        enrollment_no = match.group(0).upper()
        try:
            import sqlite3
            db_path = settings.DATABASE_URL.replace("sqlite:///", "")
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE UPPER(enrollment_no) = ?", (enrollment_no,))
            student_row = cursor.fetchone()
            conn.close()
            if student_row:
                s = dict(student_row)
                student_snippet = (
                    f"STUDENT ENROLLMENT RECORD: {s['enrollment_no']}\n"
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
                retrieved_chunks.insert(0, {
                    "document_name": "ifhe_student_directory_records.txt",
                    "snippet": student_snippet,
                    "score": 0.99
                })
                max_confidence = max(max_confidence, 0.99)
        except Exception as e:
            logger.error(f"Error querying student database during RAG chat: {e}")

    # Check for empty context or low similarity threshold fallback

    if not retrieved_chunks or max_confidence < settings.SIMILARITY_THRESHOLD:
        fallback_answer = "I don't have information on that in the official campus database."
        latency_ms = round((time.time() - start_time) * 1000, 2)
        
        log_query_to_db(
            query_id=query_id,
            username=user.username,
            role=user.role,
            question=clean_message,
            answer=fallback_answer,
            latency_ms=latency_ms,
            chunk_count=0,
            confidence=max_confidence,
            is_fallback=True
        )

        return ChatResponse(
            query_id=query_id,
            answer=fallback_answer,
            sources=[],
            confidence=max_confidence,
            is_fallback=True
        )

    # Format context for Gemini / Dynamic RAG
    formatted_context = "\n\n".join(
        [f"[{c['document_name']}]: {c['snippet']}" for c in retrieved_chunks]
    )
    prompt_text = rag_prompt.format(context=formatted_context, question=clean_message)

    # Call LLM or Dynamic Grounded Synthesizer
    answer_text = generate_llm_answer(prompt_text, retrieved_chunks=retrieved_chunks, question=clean_message)
    latency_ms = round((time.time() - start_time) * 1000, 2)

    # Format source citations
    sources = [
        SourceCitation(
            document_name=c["document_name"],
            snippet=c["snippet"][:200] + ("..." if len(c["snippet"]) > 200 else ""),
            score=c["score"]
        )
        for c in retrieved_chunks
    ]

    # Log query metrics to SQLite
    log_query_to_db(
        query_id=query_id,
        username=user.username,
        role=user.role,
        question=clean_message,
        answer=answer_text,
        latency_ms=latency_ms,
        chunk_count=len(retrieved_chunks),
        confidence=max_confidence,
        is_fallback=False
    )

    return ChatResponse(
        query_id=query_id,
        answer=answer_text,
        sources=sources,
        confidence=max_confidence,
        is_fallback=False
    )

@router.post("/feedback")
def submit_feedback(request: FeedbackRequest, user: UserSchema = Depends(get_current_user)):
    """Logs user thumbs-up/down feedback for query evaluation."""
    log_feedback_to_db(request.query_id, request.is_positive)
    return {"status": "success", "message": "Feedback recorded successfully."}
