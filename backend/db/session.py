"""
Database Connection & Session Management for CampusMIND 2.0.
Provides unified SQLAlchemy 2.x session abstraction supporting both SQLite
(for local development/testing) and PostgreSQL (for production deployments).
"""
import os
import sqlite3
from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from core.config import settings
from core.logging import logger
from db.base import Base

_engine_cache = {}


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enforces SQLite foreign key constraints upon connection initialization."""
    if type(dbapi_connection).__module__ == "sqlite3":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_engine(database_url: Optional[str] = None) -> Engine:
    """
    Returns or instantiates a SQLAlchemy engine configured for the active database URL.
    Supports SQLite and PostgreSQL.
    """
    url = database_url or settings.DATABASE_URL
    if url in _engine_cache:
        return _engine_cache[url]

    if url.startswith("sqlite:///"):
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            pool_pre_ping=settings.DB_POOL_PRE_PING,
            echo=False,
        )
    elif url.startswith("postgresql://") or url.startswith("postgresql+psycopg2://"):
        engine = create_engine(
            url,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_pre_ping=settings.DB_POOL_PRE_PING,
            echo=False,
        )
    else:
        engine = create_engine(url, pool_pre_ping=settings.DB_POOL_PRE_PING, echo=False)

    _engine_cache[url] = engine
    return engine


def check_database_health(database_url: Optional[str] = None) -> tuple[bool, str]:
    """
    Executes a lightweight ping check to verify database connectivity.
    Returns (is_healthy, status_details).
    """
    try:
        engine = get_engine(database_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        dialect = "postgresql" if settings.DATABASE_URL.startswith("postgresql") else "sqlite"
        return True, f"connected ({dialect})"
    except Exception as e:
        logger.error(f"Database health ping failed: {e}")
        return False, f"unhealthy: {str(e)}"



def get_session_factory(database_url: Optional[str] = None) -> sessionmaker:
    """Returns a sessionmaker configured with the active engine."""
    engine = get_engine(database_url)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session(database_url: Optional[str] = None) -> Generator[Session, None, None]:
    """
    Context manager providing an isolated database session with explicit transaction lifecycle.
    Commits on successful block completion, rolls back on exception, and ensures closure.
    """
    SessionLocal = get_session_factory(database_url)
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a database session per HTTP request.
    Ensures proper cleanup after request completion.
    """
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_tables(database_url: Optional[str] = None) -> None:
    """Creates all defined ORM tables in the database if they do not already exist."""
    engine = get_engine(database_url)
    Base.metadata.create_all(bind=engine)


def get_db_path() -> str:
    """Legacy helper returning absolute path for SQLite database file if applicable."""
    url = settings.DATABASE_URL
    if url.startswith("sqlite:///"):
        path = url.replace("sqlite:///", "", 1)
        return os.path.abspath(path)
    return url


def get_db_connection() -> sqlite3.Connection:
    """
    Legacy DB connection helper retained for direct SQLite connection compatibility.
    """
    db_file = get_db_path()
    os.makedirs(os.path.dirname(db_file) if os.path.dirname(db_file) else ".", exist_ok=True)
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn
