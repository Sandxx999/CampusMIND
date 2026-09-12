"""
Hybrid Retrieval & Server-Side Access Control Engine for CampusMIND 2.0.

Combines vector similarity search and keyword match ranking with strict server-side RBAC metadata
filtering, candidate deduplication, reranking, and evidence quality signals.
"""
import os
import re
from typing import List, Dict, Any, Tuple, Optional
from core.config import settings
from core.logging import logger
from rag.vector_store import get_vector_store, VectorStore
from rag.reranker import DeterministicHybridReranker, evaluate_evidence_quality

PRIVATE_STUDENT_RECORD_DOCUMENTS = {
    "ifhe_student_directory_records.txt",
    "student_directory_records.txt",
    "student_records.txt"
}


class HybridCampusRetriever:
    """
    Production hybrid retrieval engine combining vector similarity, keyword matching,
    strict server-side audience authorization filters, and evidence quality scoring.
    """

    def __init__(self, vector_store: Optional[VectorStore] = None):
        self.vector_store = vector_store or get_vector_store()
        self.reranker = DeterministicHybridReranker()

    def _build_role_audience_filter(self, user_role: str) -> List[str]:
        """Maps authenticated user role to permitted audience values."""
        role_clean = (user_role or "student").strip().lower()

        if role_clean == "student":
            return ["all", "student", "students"]
        elif role_clean == "faculty":
            return ["all", "student", "students", "faculty"]
        elif role_clean == "admin":
            return ["all", "student", "students", "faculty", "admin"]
        else:
            return ["all", "student", "students"]

    def retrieve_chunks(
        self,
        query: str,
        user_role: str,
        top_k: int = None,
        threshold: float = None,
        category_filter: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], float]:
        """
        Backwards-compatible retrieval signature returning (retrieved_sources, max_confidence_score).
        Applies role-aware security boundaries and similarity thresholding.
        """
        top_evidence, quality, max_confidence = self.retrieve_hybrid_evidence(
            query=query,
            user_role=user_role,
            top_k=top_k,
            threshold=threshold,
            category_filter=category_filter,
        )
        return top_evidence, max_confidence

    def retrieve_hybrid_evidence(
        self,
        query: str,
        user_role: str,
        top_k: int = None,
        threshold: float = None,
        category_filter: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], str, float]:
        """
        Full hybrid retrieval pipeline:
        Query -> Authorization Filter -> Vector Candidate Retrieval -> Lexical Match Scoring -> Reranking -> Evidence Quality.
        Returns: (top_evidence, evidence_quality_level, max_confidence_score).
        """
        k = top_k or settings.RETRIEVAL_TOP_K
        min_thresh = threshold or settings.SIMILARITY_THRESHOLD
        role_clean = (user_role or "student").strip().lower()

        # Query vector store for candidates (request extra candidates for reranking)
        try:
            results = self.vector_store.query(
                query_text=query,
                n_results=min(k * 3, 20),
            )
        except Exception as e:
            logger.error(f"Vector store query error: {e}")
            return [], "insufficient", 0.0

        candidates = []
        if results and results.get("documents") and len(results["documents"][0]) > 0:
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0] if "distances" in results and results["distances"] else [0.5] * len(documents)

            permitted_audiences = self._build_role_audience_filter(role_clean)

            for doc_text, meta, dist in zip(documents, metadatas, distances):
                # Calculate normalized similarity from cosine distance
                similarity = max(0.0, min(1.0, 1.0 - dist if dist <= 1.0 else 1.0 - (dist / 2.0)))

                doc_name = meta.get("document_name") or meta.get("title") or "Campus Document"
                doc_name_lower = doc_name.lower()
                raw_audience = meta.get("audience") or meta.get("allowed_roles") or "all"
                allowed_roles = [r.strip().lower() for r in raw_audience.split(",")]

                # HARD SECURITY RULE: Students can NEVER retrieve private student record documents via RAG
                if role_clean == "student" and (
                    doc_name_lower in PRIVATE_STUDENT_RECORD_DOCUMENTS
                    or meta.get("category") == "student_records"
                ):
                    logger.warning(f"BLOCKED: Unauthorized attempt by student to retrieve private record '{doc_name}' via RAG.")
                    continue

                # Server-side RBAC audience filter
                if role_clean != "admin":
                    role_authorized = any(r in permitted_audiences for r in allowed_roles) or "all" in allowed_roles
                    if not role_authorized:
                        logger.warning(f"BLOCKED: Role '{role_clean}' unauthorized for document '{doc_name}' (Audience: {raw_audience}).")
                        continue

                # Category filter if supplied
                if category_filter and meta.get("category") != category_filter:
                    continue

                candidates.append({
                    "document_id": meta.get("document_id", "doc_unknown"),
                    "document_name": doc_name,
                    "section": meta.get("section", "General"),
                    "category": meta.get("category", "general"),
                    "version": meta.get("version", "1.0"),
                    "snippet": doc_text,
                    "score": round(similarity, 3),
                    "allowed_roles": raw_audience,
                })

        if not candidates:
            return [], "insufficient", 0.0

        # Rerank candidates using hybrid reranker
        reranked_evidence = self.reranker.rerank(query, candidates, top_k=k)

        # Filter out items below threshold
        filtered_evidence = [c for c in reranked_evidence if c["score"] >= min_thresh or c.get("rerank_score", 0.0) >= min_thresh]

        # Evaluate evidence quality
        quality_level, max_score = evaluate_evidence_quality(filtered_evidence, min_threshold=min_thresh)

        return filtered_evidence, quality_level, max_score


_retriever_instance = None


def get_retriever() -> HybridCampusRetriever:
    """Lazy loader for HybridCampusRetriever instance."""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = HybridCampusRetriever()
    return _retriever_instance


# Fallback property getter for backwards compatibility
class _LazyRetrieverProxy:
    def __getattr__(self, name):
        return getattr(get_retriever(), name)


retriever_instance = _LazyRetrieverProxy()
