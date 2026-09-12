"""
Backwards-compatibility module for logger and audit helper functions.
Delegates persistence calls to AuditRepository and logging to core.logging.
"""
import os
from core.config import settings
from core.logging import logger
from repositories.audit_repository import audit_repository

DB_PATH = settings.DATABASE_URL.replace("sqlite:///", "")


def init_db():
    audit_repository.init_db()


def log_query_to_db(query_id: str, username: str, role: str, question: str, answer: str, latency_ms: float, chunk_count: int, confidence: float, is_fallback: bool):
    audit_repository.log_query(query_id, username, role, question, answer, latency_ms, chunk_count, confidence, is_fallback)


def log_feedback_to_db(query_id: str, is_positive: bool):
    audit_repository.log_feedback(query_id, is_positive)


def get_query_owner(query_id: str) -> str:
    return audit_repository.get_query_owner(query_id)


__all__ = ["logger", "init_db", "log_query_to_db", "log_feedback_to_db", "get_query_owner", "DB_PATH"]
