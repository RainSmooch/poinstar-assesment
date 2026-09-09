import json
import math
import re
from pathlib import Path
from typing import List, Dict, Any

from src.config import CHUNKS_PATH

class KnowledgeBaseRetriever:
    def __init__(self, chunks_path: Path = CHUNKS_PATH):
        self.chunks_path = chunks_path
        self.chunks: List[Dict[str, Any]] = []
        self.doc_freqs: Dict[str, int] = {}
        self.doc_lens: List[int] = []
        self.avg_dl: float = 0.0
        self.tokenized_docs: List[List[str]] = []
        self._loaded = False

    def _tokenize(self, text: str) -> List[str]:
        words = re.findall(r'[a-zA-Z0-9]+', text.lower())
        return words

    def load(self):
        if not self.chunks_path.exists():
            return
        with open(self.chunks_path, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)
            
        self.tokenized_docs = [self._tokenize(c["text"]) for c in self.chunks]
        self.doc_lens = [len(doc) for doc in self.tokenized_docs]
        total_docs = len(self.chunks)
        self.avg_dl = sum(self.doc_lens) / max(total_docs, 1)

        self.doc_freqs = {}
        for doc in self.tokenized_docs:
            unique_words = set(doc)
            for w in unique_words:
                self.doc_freqs[w] = self.doc_freqs.get(w, 0) + 1
        self._loaded = True

    def search(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        if not self._loaded:
            self.load()
        if not self.chunks:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        k1 = 1.5
        b = 0.75
        N = len(self.chunks)
        scores = []

        for idx, doc_tokens in enumerate(self.tokenized_docs):
            doc_len = self.doc_lens[idx]
            token_counts = {}
            for t in doc_tokens:
                token_counts[t] = token_counts.get(t, 0) + 1

            score = 0.0
            for q in query_tokens:
                if q in token_counts:
                    tf = token_counts[q]
                    df = self.doc_freqs.get(q, 0)
                    idf = math.log(1.0 + (N - df + 0.5) / (df + 0.5))
                    score += idf * (tf * (k1 + 1.0)) / (tf + k1 * (1.0 - b + b * (doc_len / self.avg_dl)))

            chunk = self.chunks[idx]
            query_lower = query.lower()
            
            # Berikan bobot lebih untuk bab inti naskah dibanding daftar isi
            if "BAGIAN AWAL" in chunk["chapter"]:
                score *= 0.4
            else:
                score *= 1.3

            if query_lower in chunk["text"].lower():
                score += 5.0
            if any(term in chunk["chapter"].lower() for term in query_tokens):
                score += 2.0

            scores.append((score, chunk))

        scores.sort(key=lambda x: x[0], reverse=True)
        results = [item[1] for item in scores[:top_k] if item[0] > 0]
        return results

_global_retriever = None

def search_knowledge_base(query: str, top_k: int = 2) -> List[Dict[str, Any]]:
    global _global_retriever
    if _global_retriever is None:
        _global_retriever = KnowledgeBaseRetriever()
    return _global_retriever.search(query, top_k=top_k)

def format_kb_context(results: List[Dict[str, Any]]) -> str:
    """Format ringkas dan tajam untuk mempercepat Time To First Token."""
    if not results:
        return "Tidak ditemukan kutipan spesifik dalam dokumen pedoman."
    
    formatted = []
    for idx, r in enumerate(results, 1):
        book_info = f", Hlm. {r['book_page']}" if r.get('book_page') else ""
        header = f"[{idx}] {r['chapter']} (PDF p.{r['pdf_page']}{book_info})"
        snippet = r['text'][:550].strip() + ("..." if len(r['text']) > 550 else "")
        formatted.append(f"{header}\nKaidah:\n{snippet}")
    return "\n\n".join(formatted)
