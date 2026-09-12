import logging
import sqlite3
import time
import os
from config import settings

# Configure standard console logger
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("CampusMind")

DB_PATH = settings.DATABASE_URL.replace("sqlite:///", "")

def init_db():
    """
    Initializes SQLite tables for query usage logging and user feedback.
    Separated to ensure audit trails for enterprise compliance.
    """
    db_file = os.path.abspath(DB_PATH)
    os.makedirs(os.path.dirname(db_file) if os.path.dirname(db_file) else ".", exist_ok=True)
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Query logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS query_logs (
        id TEXT PRIMARY KEY,
        timestamp TEXT,
        username TEXT,
        role TEXT,
        question TEXT,
        answer TEXT,
        latency_ms REAL,
        chunk_count INTEGER,
        confidence REAL,
        is_fallback INTEGER
    )
    """)
    
    # Feedback table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS query_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_id TEXT,
        is_positive INTEGER,
        timestamp TEXT,
        FOREIGN KEY(query_id) REFERENCES query_logs(id)
    )
    """)
    
    conn.commit()
    conn.close()

# Auto-initialize DB on import
try:
    init_db()
except Exception as e:
    logger.error(f"Failed to initialize SQLite log database: {e}")

def log_query_to_db(query_id: str, username: str, role: str, question: str, answer: str, latency_ms: float, chunk_count: int, confidence: float, is_fallback: bool):
    """Logs query execution details to SQLite for auditing and admin metrics."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO query_logs (id, timestamp, username, role, question, answer, latency_ms, chunk_count, confidence, is_fallback)
               VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?)""",
            (query_id, username, role, question, answer, latency_ms, chunk_count, confidence, 1 if is_fallback else 0)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error writing query log to database: {e}")

def log_feedback_to_db(query_id: str, is_positive: bool):
    """Logs user thumbs-up/thumbs-down feedback."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO query_feedback (query_id, is_positive, timestamp)
               VALUES (?, ?, datetime('now'))""",
            (query_id, 1 if is_positive else 0)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error writing feedback to database: {e}")

def get_query_owner(query_id: str):
    """Returns the owning username for a query, or None when it is absent/unavailable."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM query_logs WHERE id = ?", (query_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        logger.error(f"Error reading query owner: {e}")
        return None
