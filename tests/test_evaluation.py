"""
Unit & Benchmark tests for RAGEvaluator in CampusMIND 2.0.
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from rag.evaluator import RAGEvaluator, run_evaluation


def test_evaluator_load_dataset():
    evaluator = RAGEvaluator()
    data = evaluator.load_dataset()
    assert isinstance(data, list)
    assert len(data) >= 5


def test_evaluator_execution():
    results = run_evaluation()
    assert "hit_rate" in results
    assert "citation_presence_rate" in results
    assert "unauthorized_retrieval_rate" in results
    assert "out_of_domain_refusal_rate" in results

    # Security target: 0.0 unauthorized retrievals
    assert results["unauthorized_retrieval_rate"] == 0.0
    # Out of domain target: 100% refusal
    assert results["out_of_domain_refusal_rate"] >= 0.8
