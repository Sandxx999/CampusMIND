"""
Database Connection & Session Factory for CampusMIND.
Provides isolated database access for SQLite (current Phase 1 baseline)
with clean extension points for PostgreSQL (Phase 2 migration target).
"""
import os
import sqlite3
from typing import Generator
from core.config import settings
from core.logging import logger


def get_db_path() -> str:
    """Returns the absolute file path for the active SQLite database."""
    url = settings.DATABASE_URL
    if url.startswith("sqlite:///"):
        path = url.replace("sqlite:///", "", 1)
        return os.path.abspath(path)
    return url


def get_db_connection() -> sqlite3.Connection:
    """
    Returns an active SQLite database connection with row factory configured.
    Respects current settings.DATABASE_URL dynamic overrides from test fixtures.
    """
    db_file = get_db_path()
    os.makedirs(os.path.dirname(db_file) if os.path.dirname(db_file) else ".", exist_ok=True)
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    FastAPI dependency yielding a database connection per request.
    Ensures connection is safely closed after request lifecycle.
    """
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()
