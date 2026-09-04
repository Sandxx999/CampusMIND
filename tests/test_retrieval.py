import sys
import os
import json
import pytest

# Ensure backend folder is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from rag.chunker import chunk_text_documents

def test_chunker_basic():
    sample_doc = [{
        "name": "test_doc.txt",
        "content": "Line 1 paragraph.\n\nLine 2 paragraph with more text.",
        "allowed_roles": "student,faculty"
    }]
    
    chunks = chunk_text_documents(sample_doc, chunk_size=50, chunk_overlap=10)
    assert len(chunks) > 0
    assert chunks[0]["metadata"]["document_name"] == "test_doc.txt"
    assert chunks[0]["metadata"]["allowed_roles"] == "student,faculty"

def test_eval_qa_dataset_structure():
    eval_file = os.path.join(os.path.dirname(__file__), 'eval_qa_pairs.json')
    assert os.path.exists(eval_file)
    
    with open(eval_file, 'r', encoding='utf-8') as f:
        qa_pairs = json.load(f)
        
    assert isinstance(qa_pairs, list)
    assert len(qa_pairs) >= 5
    for pair in qa_pairs:
        assert "question" in pair
        assert "expected_answer" in pair
        assert "min_role" in pair
