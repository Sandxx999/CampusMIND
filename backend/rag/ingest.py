import os
import glob
from rag.chunker import chunk_text_documents
from rag.retriever import retriever_instance
from logs.logger import logger

DATA_RAW_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw"))

def ingest_campus_data():
    """
    Reads raw campus documents from data/raw, chunks them, and stores them in ChromaDB.
    """
    logger.info(f"Starting ingestion from directory: {DATA_RAW_DIR}")
    
    files = glob.glob(os.path.join(DATA_RAW_DIR, "*.txt"))
    if not files:
        logger.warning(f"No raw .txt files found in {DATA_RAW_DIR}")
        return

    documents = []
    for file_path in files:
        doc_name = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Simple metadata assignment based on file convention
        role_scope = "student,faculty,admin"
        if doc_name.lower() == "ifhe_student_directory_records.txt":
            # Individual student records are never a general student RAG corpus.
            role_scope = "faculty,admin"
        elif "faculty" in doc_name.lower():
            role_scope = "faculty,admin"
        elif "admin" in doc_name.lower():
            role_scope = "admin"

        documents.append({
            "name": doc_name,
            "content": content,
            "allowed_roles": role_scope
        })

    chunks = chunk_text_documents(documents)
    logger.info(f"Created {len(chunks)} text chunks for ingestion.")

    ids = [c["id"] for c in chunks]
    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    # Ingest into ChromaDB
    retriever_instance.collection.upsert(
        ids=ids,
        documents=texts,
        metadatas=metadatas
    )
    logger.info("Successfully ingested all chunks into ChromaDB!")

if __name__ == "__main__":
    ingest_campus_data()
