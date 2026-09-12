from typing import List, Dict

class RecursiveCharacterTextSplitter:
    """Lightweight, deterministic character text splitter with separator boundary awareness."""

    def __init__(self, chunk_size=500, chunk_overlap=80, separators=None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]

    def split_text(self, text: str) -> List[str]:
        if not text:
            return []
        
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            if end < text_len:
                # Try splitting at separator
                split_at = -1
                for sep in self.separators:
                    if not sep:
                        continue
                    idx = text.rfind(sep, start, end)
                    if idx > start:
                        split_at = idx + len(sep)
                        break
                if split_at > start:
                    end = split_at

            chunk = text[start:end]
            if chunk:
                chunks.append(chunk)
            
            if end >= text_len:
                break
            
            next_start = end - self.chunk_overlap
            start = next_start if next_start > start else end

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
