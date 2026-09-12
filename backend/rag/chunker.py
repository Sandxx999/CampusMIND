"""
Intelligent Institutional Chunker for CampusMIND 2.0.

Splits institutional campus documents into context-preserving semantic chunks while respecting
headings, paragraphs, lists, and section boundaries. Generates deterministic chunk IDs
and metadata enrichment for vector storage.
"""
import re
import hashlib
from typing import List, Dict, Any, Optional


class InstitutionalChunker:
    """Production chunker designed for institutional academic and administrative documents."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 80):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _split_into_sections(self, text: str) -> List[Dict[str, str]]:
        """Splits document text by markdown headings or double newlines into section blocks."""
        lines = text.split("\n")
        sections = []
        current_title = "General"
        current_lines = []

        for line in lines:
            # Detect Markdown headings or UPPERCASE Section Titles
            if re.match(r"^#{1,4}\s+(.*)", line) or re.match(r"^[A-Z0-9\s\-\.\:\(\)]{4,60}$", line.strip()) and len(line.strip()) > 3 and not line.strip().startswith("-"):
                if current_lines:
                    sections.append({
                        "section_title": current_title,
                        "text": "\n".join(current_lines).strip()
                    })
                    current_lines = []
                current_title = re.sub(r"^#{1,4}\s+", "", line).strip()
            else:
                current_lines.append(line)

        if current_lines:
            sections.append({
                "section_title": current_title,
                "text": "\n".join(current_lines).strip()
            })

        return sections

    def _sub_chunk_text(self, text: str) -> List[str]:
        """Splits text section into overlap-bounded chunks preserving paragraph boundaries."""
        if not text:
            return []

        if len(text) <= self.chunk_size:
            return [text]

        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para_str = para.strip()
            if not para_str:
                continue

            if len(current_chunk) + len(para_str) + 2 <= self.chunk_size:
                current_chunk = f"{current_chunk}\n\n{para_str}".strip() if current_chunk else para_str
            else:
                if current_chunk:
                    chunks.append(current_chunk)

                # Handle paragraphs larger than chunk_size
                if len(para_str) > self.chunk_size:
                    words = para_str.split(" ")
                    sub_chunk = ""
                    for word in words:
                        if len(sub_chunk) + len(word) + 1 <= self.chunk_size:
                            sub_chunk = f"{sub_chunk} {word}".strip() if sub_chunk else word
                        else:
                            if sub_chunk:
                                chunks.append(sub_chunk)
                            sub_chunk = word
                    if sub_chunk:
                        current_chunk = sub_chunk
                    else:
                        current_chunk = ""
                else:
                    current_chunk = para_str

        if current_chunk:
            chunks.append(current_chunk)

        # Apply overlap where possible
        final_chunks = []
        for i, c in enumerate(chunks):
            if i > 0 and len(c) < self.chunk_size and self.chunk_overlap > 0:
                prev_text = chunks[i - 1]
                overlap_text = prev_text[-self.chunk_overlap:]
                c_with_overlap = f"{overlap_text}\n{c}".strip()
                final_chunks.append(c_with_overlap)
            else:
                final_chunks.append(c)

        return final_chunks

    def chunk_document(self, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunks a raw document dict into enriched chunk objects.
        Expected doc dict fields:
          - id / document_id
          - name / document_name / title
          - content
          - category
          - version
          - audience / allowed_roles
          - checksum
          - source_path
        """
        content = doc.get("content", "")
        if not content:
            return []

        doc_name = doc.get("name") or doc.get("title") or "Unknown Document"
        doc_id = doc.get("id") or doc.get("document_id") or hashlib.md5(doc_name.encode()).hexdigest()[:10]
        version = doc.get("version", "1.0")
        category = doc.get("category", "general")
        audience = doc.get("audience") or doc.get("allowed_roles") or "all"
        source_path = doc.get("source_path") or doc.get("file_path") or doc_name
        checksum = doc.get("checksum") or hashlib.sha256(content.encode("utf-8")).hexdigest()

        sections = self._split_into_sections(content)
        chunked_results = []
        global_chunk_idx = 0

        for sec in sections:
            sec_title = sec["section_title"]
            sec_chunks = self._sub_chunk_text(sec["text"])

            for text_chunk in sec_chunks:
                if len(text_chunk.strip()) < 15 and len(sec_chunks) > 1:
                    continue  # Skip trivial fragments

                chunk_id = f"{doc_id}_v{version}_chk_{global_chunk_idx}"

                chunked_results.append({
                    "id": chunk_id,
                    "text": text_chunk.strip(),
                    "metadata": {
                        "document_id": str(doc_id),
                        "document_name": str(doc_name),
                        "title": str(doc_name),
                        "version": str(version),
                        "category": str(category),
                        "section": str(sec_title),
                        "audience": str(audience),
                        "allowed_roles": str(audience),  # Backwards compatibility
                        "source_path": str(source_path),
                        "checksum": str(checksum),
                        "chunk_index": int(global_chunk_idx),
                    }
                })
                global_chunk_idx += 1

        return chunked_results


def chunk_text_documents(
    documents: List[Dict[str, Any]], chunk_size: int = 500, chunk_overlap: int = 80
) -> List[Dict[str, Any]]:
    """
    Backwards-compatible convenience function for chunking document list.
    """
    chunker = InstitutionalChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    results = []
    for doc in documents:
        results.extend(chunker.chunk_document(doc))
    return results
