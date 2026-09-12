"""
RAG Evaluation Framework for CampusMIND 2.0.

Evaluates institutional knowledge retrieval hit rates, source relevance, evidence quality,
citation presence, unauthorized access security, and out-of-domain refusal rates.
"""
import os
import json
from typing import Dict, Any, List
from core.logging import logger
from rag.retriever import get_retriever
from services.chat_service import chat_service
from models.schemas import ChatRequest, UserSchema

EVAL_DATASET_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../tests/eval_qa_pairs.json"))


class RAGEvaluator:
    """Evaluation harness for benchmark evaluation of CampusMIND RAG performance."""

    def __init__(self, dataset_path: str = EVAL_DATASET_PATH):
        self.dataset_path = dataset_path
        self.retriever = get_retriever()

    def load_dataset(self) -> List[Dict[str, Any]]:
        """Loads evaluation Q&A benchmark pairs."""
        if not os.path.isfile(self.dataset_path):
            logger.error(f"Eval dataset file not found: {self.dataset_path}")
            return []

        with open(self.dataset_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def evaluate_benchmark(self) -> Dict[str, Any]:
        """
        Executes benchmark evaluation suite across all test pairs.
        Returns detailed summary metrics.
        """
        qa_pairs = self.load_dataset()
        if not qa_pairs:
            return {"error": "Empty evaluation dataset."}

        total_queries = len(qa_pairs)
        hit_count = 0
        citation_count = 0
        unauthorized_retrievals = 0
        ood_refusals = 0
        total_ood = 0

        eval_results = []

        for pair in qa_pairs:
            query = pair["question"]
            expected_doc = pair.get("expected_document")
            min_role = pair.get("min_role", "student")
            is_ood = pair.get("is_out_of_domain", False)

            mock_user = UserSchema(username=f"eval_{min_role}", role=min_role)
            req = ChatRequest(message=query)

            # Process through RAG service pipeline
            response = chat_service.process_chat_query(req, mock_user)

            # Check hit rate
            retrieved_docs = [s.document_name for s in response.sources]
            hit = False
            if expected_doc:
                hit = any(expected_doc in d for d in retrieved_docs)
                if hit:
                    hit_count += 1
            elif is_ood:
                hit = response.is_fallback or "don't have information" in response.answer.lower()
                if hit:
                    hit_count += 1

            if is_ood:
                total_ood += 1
                if response.is_fallback or "don't have information" in response.answer.lower():
                    ood_refusals += 1

            # Check citation presence
            if len(response.sources) > 0 or response.is_fallback:
                citation_count += 1

            # Check unauthorized retrieval (e.g. student retrieving admin docs)
            if min_role == "student":
                for doc in retrieved_docs:
                    if "faculty" in doc.lower() or "admin" in doc.lower() or "directory" in doc.lower():
                        unauthorized_retrievals += 1

            eval_results.append({
                "id": pair.get("id"),
                "question": query,
                "expected_document": expected_doc,
                "retrieved_documents": retrieved_docs,
                "hit": hit,
                "evidence_quality": response.evidence_quality,
                "confidence": response.confidence,
                "is_fallback": response.is_fallback,
            })

        metrics = {
            "total_queries": total_queries,
            "hit_rate": round(hit_count / total_queries if total_queries else 0.0, 3),
            "citation_presence_rate": round(citation_count / total_queries if total_queries else 0.0, 3),
            "unauthorized_retrieval_rate": round(unauthorized_retrievals / total_queries if total_queries else 0.0, 3),
            "out_of_domain_refusal_rate": round(ood_refusals / total_ood if total_ood else 1.0, 3),
            "eval_results": eval_results,
        }

        return metrics


def run_evaluation() -> Dict[str, Any]:
    evaluator = RAGEvaluator()
    results = evaluator.evaluate_benchmark()
    logger.info(f"RAG Evaluation complete: Hit Rate={results.get('hit_rate')}, Unauthorized={results.get('unauthorized_retrieval_rate')}")
    return results


if __name__ == "__main__":
    res = run_evaluation()
    print(json.dumps(res, indent=2))
