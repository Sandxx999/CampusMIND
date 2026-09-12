"""
Document Ingestion & Vector Synchronization Pipeline Engine for CampusMIND 2.0.

Provides document validation, SHA-256 checksum generation, duplicate detection, version tracking,
stale vector purging, idempotent upserting, and relational metadata synchronization.
"""
import os
import glob
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple, Optional
from core.logging import logger
from rag.chunker import InstitutionalChunker
from rag.vector_store import get_vector_store, VectorStore
from db.session import get_db_session
from db.models import KnowledgeDocument, User

DATA_RAW_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw"))
SUPPORTED_EXTENSIONS = {".txt", ".md"}


class DocumentIngestionEngine:
    """Production ingestion pipeline for institutional documents."""

    def __init__(self, data_dir: str = DATA_RAW_DIR, vector_store: Optional[VectorStore] = None):
        self.data_dir = os.path.abspath(data_dir)
        self.vector_store = vector_store or get_vector_store()
        self.chunker = InstitutionalChunker()

    @staticmethod
    def validate_file(file_path: str) -> Tuple[bool, str]:
        """Validates file existence, format, and readability."""
        if not os.path.isfile(file_path):
            return False, f"File does not exist: {file_path}"

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return False, f"Unsupported file extension '{ext}'. Allowed: {SUPPORTED_EXTENSIONS}"

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            if not content.strip():
                return False, "File is empty."
            return True, "Valid"
        except Exception as e:
            return False, f"File read error: {e}"

    @staticmethod
    def compute_checksum(file_path: str) -> str:
        """Computes SHA-256 hash of file content."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    def determine_audience_and_category(self, doc_name: str) -> Tuple[str, str]:
        """Infers default audience permissions and document category from file naming conventions."""
        name_lower = doc_name.lower()
        audience = "all"
        category = "general"

        if "student_directory" in name_lower or "records.txt" in name_lower:
            audience = "faculty,admin"
            category = "student_records"
        elif "faculty" in name_lower:
            audience = "faculty,admin"
            category = "faculty_policy"
        elif "admin" in name_lower:
            audience = "admin"
            category = "administrative"
        elif "exam" in name_lower or "hall_ticket" in name_lower:
            audience = "all"
            category = "examination"
        elif "fee" in name_lower:
            audience = "all"
            category = "financial"
        elif "academic" in name_lower or "calendar" in name_lower:
            audience = "all"
            category = "academic"
        elif "hostel" in name_lower:
            audience = "all"
            category = "hostel"
        elif "placement" in name_lower:
            audience = "all"
            category = "placement"

        return audience, category

    def ingest_single_document(self, file_path: str, force: bool = False) -> Dict[str, Any]:
        """
        Ingests a single document file with change detection, versioning, and idempotency.
        """
        is_valid, reason = self.validate_file(file_path)
        if not is_valid:
            logger.warning(f"Ingestion skipped for '{file_path}': {reason}")
            return {"status": "failed", "file": file_path, "error": reason}

        doc_name = os.path.basename(file_path)
        checksum = self.compute_checksum(file_path)
        audience, category = self.determine_audience_and_category(doc_name)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        with get_db_session() as session:
            existing_doc = session.query(KnowledgeDocument).filter(
                KnowledgeDocument.file_path == file_path
            ).first()

            if not existing_doc:
                existing_doc = session.query(KnowledgeDocument).filter(
                    KnowledgeDocument.title == doc_name
                ).first()

            if existing_doc and not force:
                if existing_doc.checksum == checksum and existing_doc.is_active:
                    logger.info(f"Document '{doc_name}' checksum unchanged ({checksum[:8]}). Skipping vector creation.")
                    return {
                        "status": "unchanged",
                        "document_id": existing_doc.id,
                        "title": existing_doc.title,
                        "checksum": checksum,
                        "chunk_count": existing_doc.chunk_count,
                    }

            # If document content changed or is new, chunk and index
            doc_id = existing_doc.id if existing_doc else f"doc_{hashlib.md5(doc_name.encode()).hexdigest()[:12]}"
            current_version = float(existing_doc.version) if existing_doc and existing_doc.version else 1.0
            new_version = f"{current_version + 0.1:.1f}" if existing_doc and existing_doc.checksum != checksum else (existing_doc.version if existing_doc else "1.0")

            # Prepare document dict for chunking
            doc_dict = {
                "id": doc_id,
                "name": doc_name,
                "title": doc_name,
                "content": content,
                "category": category,
                "audience": audience,
                "version": new_version,
                "checksum": checksum,
                "source_path": file_path,
            }

            chunks = self.chunker.chunk_document(doc_dict)
            if not chunks:
                return {"status": "failed", "file": file_path, "error": "No valid chunks produced."}

            # If existing document, purge old vectors first (stale vector handling)
            if existing_doc:
                self.vector_store.delete_document_chunks(doc_id)
                self.vector_store.delete_document_chunks(doc_name)

            ids = [c["id"] for c in chunks]
            texts = [c["text"] for c in chunks]
            metadatas = [c["metadata"] for c in chunks]

            # Upsert into vector database
            try:
                self.vector_store.upsert(ids=ids, documents=texts, metadatas=metadatas)
            except Exception as e:
                logger.error(f"Vector store upsert failed for '{doc_name}': {e}")
                return {"status": "failed", "file": file_path, "error": str(e)}

            # Update or create relational DB metadata
            if existing_doc:
                existing_doc.checksum = checksum
                existing_doc.version = new_version
                existing_doc.chunk_count = len(chunks)
                existing_doc.is_active = True
                existing_doc.updated_at = datetime.now(timezone.utc)
                session.commit()
                doc_record = existing_doc
            else:
                admin_user = session.query(User).filter(User.username == "admin1").first()
                uploader_id = admin_user.id if admin_user else None

                doc_record = KnowledgeDocument(
                    id=doc_id,
                    title=doc_name,
                    file_path=file_path,
                    category=category,
                    audience=audience,
                    version=new_version,
                    checksum=checksum,
                    chunk_count=len(chunks),
                    is_active=True,
                    uploader_id=uploader_id,
                )
                session.add(doc_record)
                session.commit()

            logger.info(f"Successfully ingested '{doc_name}' (v{new_version}, {len(chunks)} chunks).")
            return {
                "status": "indexed",
                "document_id": doc_record.id,
                "title": doc_record.title,
                "version": doc_record.version,
                "checksum": checksum,
                "chunk_count": len(chunks),
            }

    def ingest_directory(self, data_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """Scans directory and ingests all matching .txt / .md files."""
        target_dir = os.path.abspath(data_dir or self.data_dir)
        
        files = glob.glob(os.path.join(target_dir, "*.txt")) + glob.glob(os.path.join(target_dir, "*.md"))
        
        logger.info(f"Raw data directory being used: {target_dir}")
        logger.info(f"Number of raw documents discovered: {len(files)}")
        logger.info(f"ChromaDB persistence directory being used: {self.vector_store.storage_dir}")
        
        if not files:
            logger.warning(f"No raw .txt / .md files found in {target_dir}")
            return []

        results = []
        success_count = 0
        for file_path in files:
            res = self.ingest_single_document(file_path)
            results.append(res)
            if res.get("status") in ("indexed", "unchanged"):
                success_count += 1
                
        logger.info(f"Successful ingestion/upsert count: {success_count}")
        return results


def ingest_campus_data(data_dir: str = DATA_RAW_DIR) -> List[Dict[str, Any]]:
    """Convenience function for starting campus document ingestion."""
    engine = DocumentIngestionEngine(data_dir=data_dir)
    return engine.ingest_directory()


if __name__ == "__main__":
    results = ingest_campus_data()
    print(f"Ingestion completed. Processed {len(results)} documents.")
