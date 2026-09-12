"""
Vector Store Abstraction Layer for CampusMIND 2.0.

Encapsulates persistent vector database operations using ChromaDB with explicit
collection initialization, document-level identity tracking, safe upsert, deletion,
stale vector purging, metadata filtering, and health monitoring.
"""
import os
from typing import Dict, List, Any, Optional
from core.config import settings
from core.logging import logger
from rag.embeddings import get_embedding_provider, EmbeddingProvider


class CustomChromaEmbeddingAdapter:
    """ChromaDB-compatible wrapper adapter for application EmbeddingProvider instances."""

    def __init__(self, provider: EmbeddingProvider):
        self.provider = provider

    def __call__(self, input: List[str]) -> List[List[float]]:
        return self.provider.embed_documents(input)

    def name(self) -> str:
        return "sentence_transformer"


class VectorStore:
    """Production vector store manager for institutional knowledge chunks."""

    def __init__(
        self,
        collection_name: str = "campus_documents",
        storage_dir: Optional[str] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
    ):
        self.collection_name = collection_name
        self.storage_dir = storage_dir or settings.CHROMA_DB_DIR
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self._client = None
        self._collection = None

    def _ensure_initialized(self):
        if self._collection is None:
            try:
                os.makedirs(self.storage_dir, exist_ok=True)
                import chromadb

                self._client = chromadb.PersistentClient(path=self.storage_dir)

                # Custom adapter wrapping application EmbeddingProvider
                embedding_fn = CustomChromaEmbeddingAdapter(self.embedding_provider)

                self._collection = self._client.get_or_create_collection(
                    name=self.collection_name,
                    embedding_function=embedding_fn,
                    metadata={"hnsw:space": "cosine"},
                )
                logger.info(f"Initialized VectorStore collection '{self.collection_name}' at {self.storage_dir}")
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB VectorStore: {e}")
                raise RuntimeError(f"VectorStore initialization failure: {e}")

    @property
    def collection(self):
        self._ensure_initialized()
        return self._collection

    def upsert(self, ids: List[str], documents: List[str], metadatas: List[Dict[str, Any]]) -> int:
        """
        Idempotent upsert of text chunks and metadata into vector store.
        Returns count of successfully stored vectors.
        """
        if not ids or not documents:
            return 0
        self._ensure_initialized()

        try:
            self._collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
            logger.info(f"Successfully upserted {len(ids)} vector records into '{self.collection_name}'.")
            return len(ids)
        except Exception as e:
            logger.error(f"Error during vector upsert in '{self.collection_name}': {e}")
            raise RuntimeError(f"VectorStore upsert error: {e}")

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes similarity search for a query string.
        Returns raw ChromaDB query response payload.
        """
        self._ensure_initialized()
        try:
            kwargs = {
                "query_texts": [query_text],
                "n_results": n_results,
            }
            if where_filter:
                kwargs["where"] = where_filter

            return self._collection.query(**kwargs)
        except Exception as e:
            logger.error(f"Error querying vector store: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}

    def delete(self, ids: List[str]) -> bool:
        """Deletes specific vector records by ID."""
        if not ids:
            return True
        self._ensure_initialized()
        try:
            self._collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} vectors from '{self.collection_name}'.")
            return True
        except Exception as e:
            logger.error(f"Error deleting vectors {ids}: {e}")
            return False

    def delete_document_chunks(self, document_id_or_name: str) -> int:
        """
        Purges all chunks associated with a specific document from vector store.
        Supports stale vector invalidation when a document is updated or deleted.
        """
        self._ensure_initialized()
        try:
            # Query chunks by document_id or document_name metadata
            results = self._collection.get(
                where={"$or": [
                    {"document_id": document_id_or_name},
                    {"document_name": document_id_or_name}
                ]}
            )
            ids_to_delete = results.get("ids", []) if results else []
            if ids_to_delete:
                self._collection.delete(ids=ids_to_delete)
                logger.info(f"Purged {len(ids_to_delete)} stale vectors for document '{document_id_or_name}'.")
                return len(ids_to_delete)
            return 0
        except Exception as e:
            logger.error(f"Error purging document chunks for '{document_id_or_name}': {e}")
            return 0

    def health_check(self) -> Dict[str, Any]:
        """Performs vector store health inspection."""
        try:
            self._ensure_initialized()
            count = self._collection.count()
            return {
                "status": "connected",
                "collection": self.collection_name,
                "total_vectors": count,
                "storage_directory": self.storage_dir,
            }
        except Exception as e:
            return {
                "status": "error",
                "collection": self.collection_name,
                "error": str(e),
            }


_vector_store_instance = None


def get_vector_store() -> VectorStore:
    """Singleton getter for application VectorStore instance."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance
