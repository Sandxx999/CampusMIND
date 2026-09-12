"""
Reranking & Evidence Quality Scoring Engine for CampusMIND 2.0.

Provides configurable candidate reranking abstractions and measurable evidence quality
assessment signals ('high', 'medium', 'low', 'insufficient').
"""
import math
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from core.config import settings
from core.logging import logger


class Reranker(ABC):
    """Abstract interface for candidate evidence reranking."""

    @abstractmethod
    def rerank(
        self, query: str, candidates: List[Dict[str, Any]], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Reranks candidate retrieved chunks and returns top_k evidence items."""
        pass


class DeterministicHybridReranker(Reranker):
    """
    Production-grade hybrid reranker combining vector cosine similarity, keyword frequency/density,
    title/section relevance, and recency/version weights.
    """

    def __init__(self, vector_weight: float = 0.6, lexical_weight: float = 0.4):
        self.vector_weight = vector_weight
        self.lexical_weight = lexical_weight

    def _compute_lexical_score(self, query: str, text: str) -> float:
        """Computes TF-IDF style term match density score between query and chunk snippet."""
        if not query or not text:
            return 0.0

        query_terms = set(re.findall(r"\w+", query.lower()))
        # Remove low-value stop words
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "to", "in", "on", "at", "for", "of", "and", "or", "what", "when", "where", "how"}
        terms = [t for t in query_terms if t not in stop_words and len(t) > 1]
        if not terms:
            terms = list(query_terms)
        if not terms:
            return 0.0

        text_lower = text.lower()
        matched = 0
        total_term_freq = 0

        for t in terms:
            count = text_lower.count(t)
            if count > 0:
                matched += 1
                total_term_freq += count

        # Coverage ratio: what fraction of query terms appear in snippet
        coverage = matched / len(terms)
        # Term density score bounded between 0 and 1
        density = min(1.0, math.log1p(total_term_freq) / 3.0)

        return round(0.7 * coverage + 0.3 * density, 3)

    def rerank(
        self, query: str, candidates: List[Dict[str, Any]], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Reranks candidates and assigns composite rerank score."""
        if not candidates:
            return []

        reranked = []
        for cand in candidates:
            vector_score = cand.get("score", 0.0)
            snippet = cand.get("snippet", "")
            title = cand.get("document_name", "")

            lexical_score = self._compute_lexical_score(query, snippet + " " + title)

            # Bonus for exact title matches
            title_bonus = 0.0
            if any(term in title.lower() for term in re.findall(r"\w+", query.lower()) if len(term) > 3):
                title_bonus = 0.05

            composite_score = (
                self.vector_weight * vector_score
                + self.lexical_weight * lexical_score
                + title_bonus
            )
            composite_score = round(min(1.0, composite_score), 3)

            cand_copy = dict(cand)
            cand_copy["rerank_score"] = composite_score
            cand_copy["lexical_score"] = lexical_score
            cand_copy["vector_score"] = vector_score
            reranked.append(cand_copy)

        # Sort descending by composite rerank score
        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
        return reranked[:top_k]


def evaluate_evidence_quality(
    top_evidence: List[Dict[str, Any]], min_threshold: float = None
) -> Tuple[str, float]:
    """
    Computes an empirical evidence quality signal ('high', 'medium', 'low', 'insufficient')
    and returns (quality_level, max_confidence_score).
    """
    threshold = min_threshold or settings.SIMILARITY_THRESHOLD
    if not top_evidence:
        return "insufficient", 0.0

    best_score = max(c.get("rerank_score", c.get("score", 0.0)) for c in top_evidence)

    if best_score < threshold:
        return "insufficient", round(best_score, 3)

    count_above_threshold = sum(
        1 for c in top_evidence if c.get("rerank_score", c.get("score", 0.0)) >= threshold
    )

    if best_score >= 0.65 and count_above_threshold >= 2:
        quality = "high"
    elif best_score >= 0.45 or count_above_threshold >= 2:
        quality = "medium"
    elif best_score >= threshold:
        quality = "low"
    else:
        quality = "insufficient"

    return quality, round(best_score, 3)
