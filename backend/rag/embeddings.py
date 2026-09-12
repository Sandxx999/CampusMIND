"""
Embedding Provider Abstraction Layer for CampusMIND 2.0.

Provides configurable embedding model providers (SentenceTransformers, Gemini, and Mock fallback)
for vector encoding of institutional campus documents and user queries.
Enforces strict production safety: never silently falls back to mock embeddings in production.
"""
from abc import ABC, abstractmethod
from typing import List
import hashlib
from core.config import settings
from core.logging import logger


class EmbeddingProvider(ABC):
    """Abstract interface for document and query embedding generators."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns the identifier of the underlying embedding model."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Returns the vector dimensionality of generated embeddings."""
        pass

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generates embedding vectors for a list of document chunks."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Generates embedding vector for a single query string."""
        pass


class MockEmbeddingProvider(EmbeddingProvider):
    """Lightweight, deterministic mock embedding provider for ultra-fast unit testing."""

    def __init__(self, dimension: int = 384):
        self._dimension = dimension

    @property
    def model_name(self) -> str:
        return "mock-deterministic-384d"

    @property
    def dimension(self) -> int:
        return self._dimension

    def _generate_vector(self, text: str) -> List[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        vec = []
        for i in range(self._dimension):
            byte_val = digest[i % len(digest)]
            norm_val = (byte_val / 255.0) * 2.0 - 1.0
            vec.append(round(norm_val, 4))
        norm = sum(x * x for x in vec) ** 0.5 or 1.0
        return [round(x / norm, 4) for x in vec]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_vector(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._generate_vector(text)


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """
    Production provider utilizing sentence-transformers for local vector generation.
    Strictly fails closed in production when unavailable, preventing silent mock fallback.
    """

    def __init__(self, model_name: str = None):
        self._model_name = model_name or settings.EMBEDDING_MODEL
        self._model = None
        self._fallback_provider = None
        self._dim = 384

    def _handle_failure(self, operation: str, error: Exception):
        if settings.is_production:
            logger.error(f"CRITICAL: Production embedding failure during {operation}: {error}")
            raise RuntimeError(f"Production embedding provider failure during {operation}: {error}")
        logger.warning(f"SentenceTransformer failure during {operation} ({error}). Falling back to MockEmbeddingProvider.")
        self._fallback_provider = MockEmbeddingProvider(dimension=384)

    def _load_model(self):
        if self._model is None and self._fallback_provider is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self._model_name)
                self._dim = self._model.get_sentence_embedding_dimension() or 384
            except (Exception, BaseException) as e:
                self._handle_failure("model loading", e)

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        if self._model is None and self._fallback_provider is None:
            self._load_model()
        return self._fallback_provider.dimension if self._fallback_provider else self._dim

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        self._load_model()
        if self._fallback_provider:
            return self._fallback_provider.embed_documents(texts)
        try:
            embeddings = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False, batch_size=8)
            return embeddings.tolist()
        except (Exception, BaseException) as e:
            self._handle_failure("document embedding", e)
            if self._fallback_provider:
                return self._fallback_provider.embed_documents(texts)
            raise

    def embed_query(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self.dimension
        self._load_model()
        if self._fallback_provider:
            return self._fallback_provider.embed_query(text)
        try:
            embedding = self._model.encode(text, convert_to_numpy=True, show_progress_bar=False, batch_size=8)
            return embedding.tolist()
        except (Exception, BaseException) as e:
            self._handle_failure("query embedding", e)
            if self._fallback_provider:
                return self._fallback_provider.embed_query(text)
            raise


def get_embedding_provider() -> EmbeddingProvider:
    """Factory function returning configured EmbeddingProvider instance."""
    provider_name = settings.EMBEDDING_PROVIDER.lower().strip()
    if provider_name in {"sentence-transformers", "sentencetransformer", "default"}:
        return SentenceTransformerEmbeddingProvider(settings.EMBEDDING_MODEL)
    elif provider_name in {"mock", "test"}:
        return MockEmbeddingProvider()
    else:
        logger.warning(f"Unknown EMBEDDING_PROVIDER '{provider_name}'. Falling back to SentenceTransformers.")
        return SentenceTransformerEmbeddingProvider(settings.EMBEDDING_MODEL)
