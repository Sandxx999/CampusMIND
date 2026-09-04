import os
import chromadb
from chromadb.utils import embedding_functions
from config import settings
from logs.logger import logger

_retriever_instance = None

class CampusRetriever:
    def __init__(self):
        os.makedirs(settings.CHROMA_DB_DIR, exist_ok=True)
        self.client = chromadb.PersistentClient(path=settings.CHROMA_DB_DIR)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL
        )
        self.collection = self.client.get_or_create_collection(
            name="campus_documents",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

    def retrieve_chunks(self, query: str, user_role: str, top_k: int = None, threshold: float = None):
        """
        Retrieves top-k relevant document chunks filtered by user role permissions.
        Filters out low-similarity chunks below the threshold to prevent hallucinations.
        """
        k = top_k or settings.RETRIEVAL_TOP_K
        min_thresh = threshold or settings.SIMILARITY_THRESHOLD

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
            )
        except Exception as e:
            logger.error(f"Error querying ChromaDB collection: {e}")
            return [], 0.0

        retrieved_sources = []
        max_score = 0.0

        if results and results.get('documents') and len(results['documents'][0]) > 0:
            documents = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results['distances'][0] if 'distances' in results and results['distances'] else [0.3]*len(documents)

            role_clean = (user_role or "student").strip().lower()

            for doc, meta, dist in zip(documents, metadatas, distances):
                # For cosine distance in ChromaDB (hnsw:space = cosine), dist ranges from 0.0 (identical) to 2.0
                # Similarity = 1.0 - dist (or max(0.0, 1.0 - dist / 2.0))
                similarity = max(0.0, min(1.0, 1.0 - dist if dist <= 1.0 else 1.0 - (dist / 2.0)))
                
                raw_roles = meta.get("allowed_roles", "student,faculty,admin")
                allowed_roles = [r.strip().lower() for r in raw_roles.split(",")]
                
                if role_clean != "admin" and role_clean not in allowed_roles:
                    continue

                if similarity >= min_thresh:
                    retrieved_sources.append({
                        "document_name": meta.get("document_name", "Campus Doc"),
                        "snippet": doc,
                        "score": round(similarity, 3)
                    })
                    if similarity > max_score:
                        max_score = similarity

        return retrieved_sources, round(max_score, 3)

def get_retriever():
    """Lazy loader for CampusRetriever instance."""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = CampusRetriever()
    return _retriever_instance

# Fallback property getter for backwards compatibility
class _LazyRetrieverProxy:
    def __getattr__(self, name):
        return getattr(get_retriever(), name)

retriever_instance = _LazyRetrieverProxy()
