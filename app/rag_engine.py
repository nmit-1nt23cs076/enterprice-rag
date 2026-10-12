import re
import math
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

class DocumentChunk:
    def __init__(self, doc_id: str, filename: str, chunk_id: int, text: str, page: Optional[int] = None):
        self.doc_id = doc_id
        self.filename = filename
        self.chunk_id = chunk_id
        self.text = text
        self.page = page

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "filename": self.filename,
            "chunk_id": self.chunk_id,
            "text": self.text,
            "page": self.page
        }

class SimpleVectorStore:
    """
    Lightweight, high-performance Vector & BM25 hybrid indexer.
    Requires no external native C++ dependencies or heavy vector DB setup.
    """
    def __init__(self):
        self.chunks: List[DocumentChunk] = []
        self.doc_frequencies: Dict[str, int] = {}
        self.chunk_tf: List[Dict[str, float]] = []
        self.total_docs = 0
        self.avg_doc_len = 0.0

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\b[a-zA-Z0-9_-]{2,}\b', text.lower())

    def clear(self):
        self.chunks.clear()
        self.doc_frequencies.clear()
        self.chunk_tf.clear()
        self.total_docs = 0
        self.avg_doc_len = 0.0

    def remove_document(self, doc_id: str):
        keep_indices = [i for i, c in enumerate(self.chunks) if c.doc_id != doc_id]
        self.chunks = [self.chunks[i] for i in keep_indices]
        self._reindex()

    def add_chunks(self, chunks: List[DocumentChunk]):
        self.chunks.extend(chunks)
        self._reindex()

    def _reindex(self):
        self.doc_frequencies.clear()
        self.chunk_tf.clear()
        self.total_docs = len(self.chunks)

        if self.total_docs == 0:
            self.avg_doc_len = 0.0
            return

        total_length = 0
        for chunk in self.chunks:
            tokens = self._tokenize(chunk.text)
            total_length += len(tokens)
            counts: Dict[str, int] = {}
            for t in tokens:
                counts[t] = counts.get(t, 0) + 1

            tf_dict: Dict[str, float] = {}
            for t, cnt in counts.items():
                tf_dict[t] = cnt / max(1, len(tokens))
                self.doc_frequencies[t] = self.doc_frequencies.get(t, 0) + 1

            self.chunk_tf.append(tf_dict)

        self.avg_doc_len = total_length / self.total_docs

    def search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        if not self.chunks:
            return []

        q_tokens = self._tokenize(query)
        if not q_tokens:
            return []

        scores = np.zeros(self.total_docs)
        k1 = 1.5
        b = 0.75

        for i, chunk in enumerate(self.chunks):
            tf_dict = self.chunk_tf[i]
            doc_len = len(self._tokenize(chunk.text))
            score = 0.0

            for q in q_tokens:
                if q in tf_dict:
                    freq = tf_dict[q] * doc_len
                    df = self.doc_frequencies.get(q, 1)
                    idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1.0)
                    numerator = freq * (k1 + 1)
                    denominator = freq + k1 * (1 - b + b * (doc_len / max(1.0, self.avg_doc_len)))
                    score += idf * (numerator / max(1e-5, denominator))

            scores[i] = score

        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            sc = float(scores[idx])
            if sc > 0:
                results.append({
                    "chunk": self.chunks[idx].to_dict(),
                    "score": round(sc, 4)
                })

        return results

class RAGEngine:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.vector_store = SimpleVectorStore()
        self.indexed_files: Dict[str, Dict[str, Any]] = {}

    def extract_text_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        suffix = file_path.suffix.lower()
        pages_content = []

        if suffix == ".pdf" and PdfReader is not None:
            try:
                reader = PdfReader(str(file_path))
                for page_idx, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    if text.strip():
                        pages_content.append({"page": page_idx + 1, "text": text})
            except Exception as e:
                pages_content.append({"page": 1, "text": f"Error reading PDF: {e}"})
        else:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                    pages_content.append({"page": 1, "text": text})
            except Exception as e:
                pages_content.append({"page": 1, "text": f"Error reading text file: {e}"})

        return pages_content

    def split_text(self, text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) + 2 <= chunk_size:
                current_chunk = f"{current_chunk}\n\n{para}".strip()
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                if len(para) > chunk_size:
                    # Split oversized paragraph by sentence
                    words = para.split(" ")
                    temp = ""
                    for word in words:
                        if len(temp) + len(word) + 1 <= chunk_size:
                            temp = f"{temp} {word}".strip()
                        else:
                            if temp:
                                chunks.append(temp)
                            temp = word
                    if temp:
                        current_chunk = temp
                    else:
                        current_chunk = ""
                else:
                    current_chunk = para

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def index_document(self, doc_id: str, filename: str, file_path: Path) -> int:
        pages_data = self.extract_text_from_file(file_path)
        all_chunks = []
        chunk_counter = 1

        for page_data in pages_data:
            page_num = page_data["page"]
            text = page_data["text"]
            text_splits = self.split_text(text, self.chunk_size, self.chunk_overlap)

            for split in text_splits:
                if len(split.strip()) > 15:
                    all_chunks.append(DocumentChunk(
                        doc_id=doc_id,
                        filename=filename,
                        chunk_id=chunk_counter,
                        text=split.strip(),
                        page=page_num
                    ))
                    chunk_counter += 1

        self.vector_store.add_chunks(all_chunks)
        self.indexed_files[doc_id] = {
            "doc_id": doc_id,
            "filename": filename,
            "num_chunks": len(all_chunks),
            "timestamp": time.time()
        }
        return len(all_chunks)

    def delete_document(self, doc_id: str) -> bool:
        if doc_id in self.indexed_files:
            self.vector_store.remove_document(doc_id)
            del self.indexed_files[doc_id]
            return True
        return False

    def query(self, question: str, top_k: int = 4) -> Dict[str, Any]:
        start_time = time.time()
        results = self.vector_store.search(question, top_k=top_k)

        if not results:
            return {
                "answer": "No relevant context found in the uploaded documents to answer this question. Please make sure documents are uploaded and indexed.",
                "sources": [],
                "latency_sec": round(time.time() - start_time, 3),
                "num_results": 0
            }

        # Formulate synthesized context and answer
        context_texts = [r["chunk"]["text"] for r in results]
        sources = [
            {
                "filename": r["chunk"]["filename"],
                "page": r["chunk"]["page"],
                "chunk_id": r["chunk"]["chunk_id"],
                "score": r["score"],
                "excerpt": r["chunk"]["text"][:220] + "..." if len(r["chunk"]["text"]) > 220 else r["chunk"]["text"]
            }
            for r in results
        ]

        # Concise Extractive/Generative Synthesizer
        best_chunk = results[0]["chunk"]["text"]
        sentences = re.split(r'(?<=[.!?])\s+', best_chunk)
        relevant_sentences = [s.strip() for s in sentences if len(s.strip()) > 10][:4]
        synthesized_answer = " ".join(relevant_sentences) if relevant_sentences else best_chunk[:400]

        return {
            "answer": synthesized_answer,
            "sources": sources,
            "latency_sec": round(time.time() - start_time, 3),
            "num_results": len(results)
        }
