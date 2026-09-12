"""
Audit & Query Log Data Repository for CampusMIND 2.0.

Encapsulates operations for query logging, feedback tracking, and administrative usage analytics.
Supports canonical relational ORM models (QueryLog & QueryFeedback) with robust legacy fallback.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import select, func, desc, text
from db.session import get_db_session, get_db_connection, create_tables, get_engine
from db.models import QueryLog, QueryFeedback, User, AuditEvent
from core.logging import logger


class AuditRepository:
    """Repository managing audit trails for queries, user feedback, and RAG usage metrics."""

    def __init__(self, db_conn_factory=get_db_connection):
        self.db_conn_factory = db_conn_factory

    def init_db(self) -> None:
        """Initializes canonical ORM tables and legacy tables with column migration checks."""
        try:
            create_tables()
        except Exception as e:
            logger.debug(f"Alembic or ORM create_tables check: {e}")

        # Ensure columns exist on SQLite database
        try:
            engine = get_engine()
            if engine.name == "sqlite":
                with engine.connect() as conn:
                    # Check columns on query_logs table
                    result = conn.execute(text("PRAGMA table_info(query_logs)"))
                    columns = [row[1] for row in result.fetchall()]
                    if "user_id" not in columns:
                        conn.execute(text("ALTER TABLE query_logs ADD COLUMN user_id VARCHAR(36)"))
                    if "created_at" not in columns:
                        conn.execute(text("ALTER TABLE query_logs ADD COLUMN created_at DATETIME"))
                    conn.commit()
        except Exception as e:
            logger.debug(f"SQLite PRAGMA column migration check: {e}")

        # Ensure legacy tables exist for fallback compatibility
        conn = self.db_conn_factory()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                timestamp TEXT,
                username TEXT,
                role TEXT,
                question TEXT,
                answer TEXT,
                latency_ms REAL,
                chunk_count INTEGER,
                confidence REAL,
                is_fallback INTEGER,
                created_at TEXT
            )
            """)
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
        except Exception as e:
            logger.error(f"Failed to initialize legacy audit database tables: {e}")
        finally:
            conn.close()

    def log_query(
        self,
        query_id: str,
        username: str,
        role: str,
        question: str,
        answer: str,
        latency_ms: float,
        chunk_count: int,
        confidence: float,
        is_fallback: bool
    ) -> None:
        """Persists a query execution record to the query_logs repository."""
        # 1. Try canonical ORM model insert
        try:
            with get_db_session() as session:
                user = session.execute(select(User).where(User.username == username)).scalar_one_or_none()
                user_id = user.id if user else None

                log_entry = QueryLog(
                    id=query_id,
                    user_id=user_id,
                    timestamp=datetime.now(timezone.utc),
                    username=username,
                    role=role,
                    question=question,
                    answer=answer,
                    latency_ms=float(latency_ms),
                    chunk_count=int(chunk_count),
                    confidence=float(confidence),
                    is_fallback=bool(is_fallback),
                )
                session.add(log_entry)
                return
        except Exception as e:
            logger.debug(f"Canonical query log insert failed, trying legacy insert: {e}")

        # 2. Legacy fallback insert for existing sqlite setups
        conn = self.db_conn_factory()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT OR REPLACE INTO query_logs (id, user_id, timestamp, username, role, question, answer, latency_ms, chunk_count, confidence, is_fallback, created_at)
                   VALUES (?, ?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
                (query_id, None, username, role, question, answer, latency_ms, chunk_count, confidence, 1 if is_fallback else 0)
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Error executing legacy log_query: {e}")
        finally:
            conn.close()

    def log_feedback(self, query_id: str, is_positive: bool) -> None:
        """Persists feedback (thumbs-up/thumbs-down) for a query."""
        # 1. Try canonical ORM insert
        try:
            with get_db_session() as session:
                fb = QueryFeedback(
                    query_id=query_id,
                    is_positive=bool(is_positive),
                    timestamp=datetime.now(timezone.utc),
                )
                session.add(fb)
                return
        except Exception as e:
            logger.debug(f"Canonical feedback insert failed, trying legacy insert: {e}")

        # 2. Legacy fallback insert
        conn = self.db_conn_factory()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO query_feedback (query_id, is_positive, timestamp)
                   VALUES (?, ?, datetime('now'))""",
                (query_id, 1 if is_positive else 0)
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Error executing legacy log_feedback: {e}")
        finally:
            conn.close()

    def get_query_owner(self, query_id: str) -> Optional[str]:
        """Retrieves username of query author, or None if query not found."""
        # 1. Try canonical ORM query
        try:
            with get_db_session() as session:
                log_entry = session.get(QueryLog, query_id)
                if log_entry:
                    return log_entry.username
        except Exception as e:
            logger.debug(f"Canonical query owner lookup failed: {e}")

        # 2. Legacy fallback query
        conn = self.db_conn_factory()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM query_logs WHERE id = ?", (query_id,))
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"Error in legacy get_query_owner: {e}")
            return None
        finally:
            conn.close()

    def get_admin_stats(self) -> Dict[str, Any]:
        """Aggregates administrative analytics and query logs summary."""
        # 1. Try canonical ORM aggregation
        try:
            with get_db_session() as session:
                total_queries = session.scalar(select(func.count(QueryLog.id))) or 0
                if total_queries > 0:
                    avg_lat = session.scalar(select(func.avg(QueryLog.latency_ms))) or 0.0
                    fallbacks = session.scalar(select(func.count(QueryLog.id)).where(QueryLog.is_fallback == True)) or 0
                    no_answer_rate = f"{(fallbacks / total_queries * 100):.1f}%"

                    pos_feedback = session.scalar(select(func.count(QueryFeedback.id)).where(QueryFeedback.is_positive == True)) or 0
                    total_feedback = session.scalar(select(func.count(QueryFeedback.id))) or 0
                    pos_pct = f"{(pos_feedback / total_feedback * 100):.1f}%" if total_feedback > 0 else "N/A"

                    recent_objs = session.scalars(
                        select(QueryLog).order_by(desc(QueryLog.timestamp)).limit(10)
                    ).all()

                    recent_logs = [
                        {
                            "query_id": q.id,
                            "timestamp": q.timestamp.isoformat() if hasattr(q.timestamp, "isoformat") else str(q.timestamp),
                            "username": q.username,
                            "role": q.role,
                            "question": q.question,
                            "latency_ms": q.latency_ms,
                            "chunk_count": q.chunk_count,
                        }
                        for q in recent_objs
                    ]

                    return {
                        "total_queries": total_queries,
                        "avg_latency_ms": round(float(avg_lat), 1),
                        "no_answer_rate": no_answer_rate,
                        "positive_feedback_pct": pos_pct,
                        "recent_logs": recent_logs,
                    }
        except Exception as e:
            logger.debug(f"Canonical admin stats aggregation failed: {e}")

        # 2. Legacy fallback aggregation
        conn = self.db_conn_factory()
        try:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM query_logs")
            total_queries = cursor.fetchone()[0] or 0

            cursor.execute("SELECT AVG(latency_ms) FROM query_logs")
            avg_latency = cursor.fetchone()[0] or 0.0

            cursor.execute("SELECT COUNT(*) FROM query_logs WHERE is_fallback = 1")
            fallbacks = cursor.fetchone()[0] or 0
            no_answer_rate = f"{(fallbacks / total_queries * 100):.1f}%" if total_queries > 0 else "0%"

            cursor.execute("SELECT COUNT(*) FROM query_feedback WHERE is_positive = 1")
            pos_feedback = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM query_feedback")
            total_feedback = cursor.fetchone()[0] or 0
            pos_pct = f"{(pos_feedback / total_feedback * 100):.1f}%" if total_feedback > 0 else "N/A"

            cursor.execute(
                "SELECT id, timestamp, username, role, question, latency_ms, chunk_count FROM query_logs ORDER BY timestamp DESC LIMIT 10"
            )
            rows = cursor.fetchall()
            recent_logs = [
                {
                    "query_id": r[0],
                    "timestamp": r[1],
                    "username": r[2],
                    "role": r[3],
                    "question": r[4],
                    "latency_ms": r[5],
                    "chunk_count": r[6],
                }
                for r in rows
            ]

            return {
                "total_queries": total_queries,
                "avg_latency_ms": round(avg_latency, 1),
                "no_answer_rate": no_answer_rate,
                "positive_feedback_pct": pos_pct,
                "recent_logs": recent_logs,
            }
        finally:
            conn.close()

    def log_audit_event(
        self,
        event_type: str,
        actor_username: str,
        user_id: Optional[str] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """Persists a security or administrative audit event."""
        import uuid
        try:
            with get_db_session() as session:
                event = AuditEvent(
                    id=f"evt_{uuid.uuid4().hex[:12]}",
                    event_type=event_type,
                    user_id=user_id,
                    actor_username=actor_username,
                    ip_address=ip_address,
                    details=details,
                    timestamp=datetime.now(timezone.utc),
                )
                session.add(event)
        except Exception as e:
            logger.debug(f"Failed to log audit event ({event_type}): {e}")

    def get_audit_events(
        self,
        actor_username: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Queries security audit events filtered by actor username or event_type."""
        try:
            with get_db_session() as session:
                stmt = select(AuditEvent)
                if actor_username:
                    stmt = stmt.where(AuditEvent.actor_username == actor_username)
                if event_type:
                    stmt = stmt.where(AuditEvent.event_type == event_type)
                stmt = stmt.order_by(desc(AuditEvent.timestamp)).limit(limit)

                events = session.scalars(stmt).all()
                return [
                    {
                        "id": e.id,
                        "event_type": e.event_type,
                        "actor_username": e.actor_username,
                        "user_id": e.user_id,
                        "ip_address": e.ip_address,
                        "details": e.details,
                        "timestamp": e.timestamp.isoformat() if hasattr(e.timestamp, "isoformat") else str(e.timestamp),
                    }
                    for e in events
                ]
        except Exception as e:
            logger.debug(f"Failed to query audit events: {e}")
            return []


audit_repository = AuditRepository()
try:
    audit_repository.init_db()
except Exception:
    pass
