"""
Unit tests for Production Embedding Safety in CampusMIND 2.0.
Verifies that:
1. Production environment (APP_ENV=production) NEVER falls back to MockEmbeddingProvider
   and instead raises an explicit RuntimeError on SentenceTransformer failure.
2. Non-production environment (APP_ENV=development/test) gracefully falls back
   to MockEmbeddingProvider when SentenceTransformer is unavailable.
"""
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from core.config import settings
from rag.embeddings import SentenceTransformerEmbeddingProvider, MockEmbeddingProvider


def test_production_embedding_failure_raises_runtime_error():
    """In production, SentenceTransformer model loading failure must raise RuntimeError and NOT fallback to Mock."""
    with patch.object(settings, 'APP_ENV', 'production'):
        assert settings.is_production is True

        provider = SentenceTransformerEmbeddingProvider("non_existent_model_for_test")

        # Mock sentence_transformers import failure by raising Exception when SentenceTransformer is instantiated
        mock_module = MagicMock()
        mock_module.SentenceTransformer.side_effect = Exception("Failed to load SentenceTransformer model")

        with patch.dict(sys.modules, {'sentence_transformers': mock_module}):
            with pytest.raises(RuntimeError) as exc_info:
                provider.embed_documents(["Hello production"])

            assert "Production embedding provider failure during model loading" in str(exc_info.value)
            assert provider._fallback_provider is None


def test_production_embed_query_failure_raises_runtime_error():
    """In production, failure during query embedding raises RuntimeError."""
    with patch.object(settings, 'APP_ENV', 'production'):
        assert settings.is_production is True

        provider = SentenceTransformerEmbeddingProvider("non_existent_model_for_test")

        mock_instance = MagicMock()
        mock_instance.encode.side_effect = Exception("Vector encoding failed")
        mock_module = MagicMock()
        mock_module.SentenceTransformer.return_value = mock_instance

        with patch.dict(sys.modules, {'sentence_transformers': mock_module}):
            with pytest.raises(RuntimeError) as exc_info:
                provider.embed_query("Search query in production")

            assert "Production embedding provider failure during query embedding" in str(exc_info.value)
            assert provider._fallback_provider is None


def test_non_production_embedding_failure_uses_mock_fallback():
    """In non-production (e.g. development), SentenceTransformer failure falls back to MockEmbeddingProvider."""
    with patch.object(settings, 'APP_ENV', 'development'):
        assert settings.is_production is False

        provider = SentenceTransformerEmbeddingProvider("non_existent_model_for_test")

        mock_module = MagicMock()
        mock_module.SentenceTransformer.side_effect = Exception("Failed to load SentenceTransformer model")

        with patch.dict(sys.modules, {'sentence_transformers': mock_module}):
            embeddings = provider.embed_documents(["Hello development"])

            assert len(embeddings) == 1
            assert len(embeddings[0]) == 384
            assert isinstance(provider._fallback_provider, MockEmbeddingProvider)


def test_non_production_embed_query_fallback():
    """In non-production, embed_query falls back gracefully to MockEmbeddingProvider."""
    with patch.object(settings, 'APP_ENV', 'development'):
        assert settings.is_production is False

        provider = SentenceTransformerEmbeddingProvider("non_existent_model_for_test")

        mock_module = MagicMock()
        mock_module.SentenceTransformer.side_effect = Exception("Failed to load SentenceTransformer model")

        with patch.dict(sys.modules, {'sentence_transformers': mock_module}):
            vec = provider.embed_query("Search query in development")

            assert len(vec) == 384
            assert isinstance(provider._fallback_provider, MockEmbeddingProvider)
