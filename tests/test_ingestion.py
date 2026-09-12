"""
Unit tests for DocumentIngestionEngine and vector store synchronization in CampusMIND 2.0.
"""
import sys
import os
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from rag.ingest import DocumentIngestionEngine
from db.session import get_db_session
from db.models import KnowledgeDocument


def test_ingestion_validation():
    engine = DocumentIngestionEngine()
    is_valid, reason = engine.validate_file("non_existent_file_path.txt")
    assert is_valid is False
    assert "does not exist" in reason


def test_ingestion_idempotency_and_versioning():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        test_file = os.path.join(tmp_dir, "test_policy.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("Initial campus policy text for testing idempotency.")

        from rag.vector_store import VectorStore
        vs = VectorStore(storage_dir=os.path.join(tmp_dir, "chroma"))
        engine = DocumentIngestionEngine(data_dir=tmp_dir, vector_store=vs)
        res1 = engine.ingest_single_document(test_file)
        assert res1["status"] in {"indexed", "unchanged"}

        # Ingest exact same document again
        res2 = engine.ingest_single_document(test_file)
        assert res2["status"] == "unchanged"

        # Modify file content
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("Updated campus policy text with new regulations added.")

        res3 = engine.ingest_single_document(test_file)
        assert res3["status"] == "indexed"
        assert res3["version"] != "1.0" or res3["checksum"] != res1["checksum"]
