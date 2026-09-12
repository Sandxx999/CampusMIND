"""
Unit tests for InstitutionalChunker in CampusMIND 2.0.
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from rag.chunker import InstitutionalChunker, chunk_text_documents


def test_institutional_chunker_basic():
    doc = {
        "id": "doc_001",
        "name": "academic_calendar.txt",
        "content": "# Academic Calendar 2024\n\nFall semester starts on August 15, 2024.\n\n## Midterm Exams\n\nMidterms run from October 1 to October 10.",
        "category": "academic",
        "audience": "student,faculty",
        "version": "1.0",
    }

    chunker = InstitutionalChunker(chunk_size=100, chunk_overlap=20)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) > 0
    assert chunks[0]["metadata"]["document_id"] == "doc_001"
    assert chunks[0]["metadata"]["category"] == "academic"
    assert chunks[0]["metadata"]["audience"] == "student,faculty"
    assert "checksum" in chunks[0]["metadata"]
    assert "chunk_index" in chunks[0]["metadata"]


def test_chunker_backwards_compatibility():
    sample_docs = [{
        "name": "test_rules.txt",
        "content": "Rule 1: Always follow campus guidelines.\nRule 2: Respect library hours.",
        "allowed_roles": "student"
    }]

    chunks = chunk_text_documents(sample_docs)
    assert len(chunks) > 0
    assert chunks[0]["metadata"]["document_name"] == "test_rules.txt"
    assert chunks[0]["metadata"]["allowed_roles"] == "student"


def test_chunker_deterministic():
    doc = {
        "id": "doc_det",
        "name": "fixed.txt",
        "content": "Section 1\nSome fixed text content for testing determinism.",
        "version": "2.0",
    }
    chunker = InstitutionalChunker()
    chunks_1 = chunker.chunk_document(doc)
    chunks_2 = chunker.chunk_document(doc)

    assert len(chunks_1) == len(chunks_2)
    for c1, c2 in zip(chunks_1, chunks_2):
        assert c1["id"] == c2["id"]
        assert c1["text"] == c2["text"]
        assert c1["metadata"] == c2["metadata"]
