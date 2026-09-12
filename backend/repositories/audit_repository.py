"""
Audit & Query Log Data Repository.
Encapsulates operations for query logging, feedback tracking, and admin analytics.
"""
from typing import Dict, Any, List, Optional
from db.session import get_db_connection
from core.logging import logger


class AuditRepository:
    """Repository managing audit trails for queries, user feedback, and RAG usage metrics."""

    def __init__(self, db_conn_factory=get_db_connection):
        self.db_conn_factory = db_conn_factory

    def init_db(self) -> None:
        """Initializes tables for query logs and feedback if they do not exist."""
        conn = self.db_conn_factory()
        try:
            cursor = conn.cursor()
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
            logger.error(f"Failed to initialize audit database tables: {e}")
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
        """Persists a query execution record to the query_logs table."""
        conn = self.db_conn_factory()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO query_logs (id, timestamp, username, role, question, answer, latency_ms, chunk_count, confidence, is_fallback)
                   VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?)""",
                (query_id, username, role, question, answer, latency_ms, chunk_count, confidence, 1 if is_fallback else 0)
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Error logging query to repository: {e}")
        finally:
            conn.close()

    def log_feedback(self, query_id: str, is_positive: bool) -> None:
        """Persists thumbs-up/thumbs-down feedback for a query."""
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
            logger.error(f"Error logging feedback to repository: {e}")
        finally:
            conn.close()

    def get_query_owner(self, query_id: str) -> Optional[str]:
        """Retrieves username of query author, or None if query not found."""
        conn = self.db_conn_factory()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM query_logs WHERE id = ?", (query_id,))
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"Error checking query owner in repository: {e}")
            return None
        finally:
            conn.close()

    def get_admin_stats(self) -> Dict[str, Any]:
        """Aggregates administrative analytics and query logs summary."""
        conn = self.db_conn_factory()
        try:
            cursor = conn.cursor()

            # Total queries
            cursor.execute("SELECT COUNT(*) FROM query_logs")
            total_queries = cursor.fetchone()[0] or 0

            # Avg latency
            cursor.execute("SELECT AVG(latency_ms) FROM query_logs")
            avg_latency = cursor.fetchone()[0] or 0.0

            # Fallback rate
            cursor.execute("SELECT COUNT(*) FROM query_logs WHERE is_fallback = 1")
            fallbacks = cursor.fetchone()[0] or 0
            no_answer_rate = f"{(fallbacks / total_queries * 100):.1f}%" if total_queries > 0 else "0%"

            # Positive feedback percentage
            cursor.execute("SELECT COUNT(*) FROM query_feedback WHERE is_positive = 1")
            pos_feedback = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM query_feedback")
            total_feedback = cursor.fetchone()[0] or 0
            pos_pct = f"{(pos_feedback / total_feedback * 100):.1f}%" if total_feedback > 0 else "N/A"

            # Recent log entries
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


audit_repository = AuditRepository()
# Auto-initialize database tables on module loading
try:
    audit_repository.init_db()
except Exception:
    pass
