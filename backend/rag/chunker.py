try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        class RecursiveCharacterTextSplitter:
            def __init__(self, chunk_size=500, chunk_overlap=80, separators=None):
                self.chunk_size = chunk_size
                self.chunk_overlap = chunk_overlap

            def split_text(self, text: str):
                chunks = []
                start = 0
                while start < len(text):
                    end = min(start + self.chunk_size, len(text))
                    chunks.append(text[start:end])
                    if end == len(text):
                        break
                    start += self.chunk_size - self.chunk_overlap
                return chunks

from typing import List, Dict

def chunk_text_documents(documents: List[Dict[str, str]], chunk_size: int = 500, chunk_overlap: int = 80) -> List[Dict]:
    """
    Splits raw text documents into semantic chunks with overlap to preserve context across boundaries.
    Attaches metadata (source doc, role permission scope, chunk_id).
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )

    chunked_results = []
    
    for doc in documents:
        raw_text = doc.get("content", "")
        doc_name = doc.get("name", "Unknown Document")
        allowed_roles = doc.get("allowed_roles", "student,faculty,admin") # Comma-separated
        
        splits = text_splitter.split_text(raw_text)
        
        for idx, text in enumerate(splits):
            chunked_results.append({
                "id": f"{doc_name}_chunk_{idx}",
                "text": text,
                "metadata": {
                    "document_name": doc_name,
                    "chunk_index": idx,
                    "allowed_roles": allowed_roles
                }
            })
            
    return chunked_results
