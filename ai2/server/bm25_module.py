"""
AI2-02: BM25 Indexing Module
Owner: AI2 - Trung
Status: Done

In-memory BM25 index over knowledge_base.json.
Built once at server startup, held in RAM.
CamelCase-aware tokenizer for JS code keyword matching.
"""

import json
import re
import time
import os
from typing import List, Dict, Any

from rank_bm25 import BM25Okapi

# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

STOPWORDS = {
    "the", "a", "an", "is", "in", "on", "at", "to", "for", "of", "and",
    "or", "with", "this", "that", "it", "be", "are", "was", "were",
    "has", "have", "had", "do", "does", "did", "not", "by", "from",
    "as", "if", "when", "then", "so", "but", "also", "can", "will",
    "use", "used", "using", "should", "would", "could", "may", "each",
    "how", "what", "which", "who", "into", "after", "before",
    "its", "their", "they", "we", "you", "he", "she", "i", "me",
}


def _split_camel(token: str) -> List[str]:
    """fetchAllUsers -> ['fetch', 'all', 'users']"""
    parts = re.sub(r"([a-z])([A-Z])", r"\1 \2", token)
    parts = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", parts)
    return parts.lower().split()


def tokenize(text: str) -> List[str]:
    """
    Tokenize text for BM25 indexing.
    Steps:
      1. Split on non-alphanumeric chars (handles snake_case, dots, parens)
      2. CamelCase split each chunk
      3. Lowercase + remove stopwords + min length 2
    """
    raw_tokens = re.split(r"[^a-zA-Z0-9]+", text)
    tokens = []
    for raw in raw_tokens:
        if not raw:
            continue
        for sub in _split_camel(raw):
            sub = sub.strip()
            if len(sub) >= 2 and sub not in STOPWORDS:
                tokens.append(sub)
    return tokens


# ---------------------------------------------------------------------------
# BM25Retriever
# ---------------------------------------------------------------------------

class BM25Retriever:
    """
    In-memory BM25 index over a list of knowledge base documents.

    Usage:
        retriever = BM25Retriever()
        retriever.build(docs)           # call once at startup
        results = retriever.search("Promise.all parallel fetch", top_k=3)
    """

    def __init__(self):
        self._index: BM25Okapi | None = None
        self._docs: List[Dict[str, Any]] = []
        self._build_time_ms: float = 0.0

    def build(self, docs: List[Dict[str, Any]]) -> None:
        """
        Build BM25 index from docs list.
        Each doc must have at least: {id, title, content, category}.
        Indexes title + content combined for richer retrieval.
        """
        start = time.perf_counter()

        self._docs = docs
        corpus = []
        for doc in docs:
            combined = f"{doc.get('title', '')} {doc.get('content', '')}"
            corpus.append(tokenize(combined))

        self._index = BM25Okapi(corpus)
        self._build_time_ms = (time.perf_counter() - start) * 1000

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search for top_k most relevant docs given a query string.
        Query is typically AST-extracted keywords from user code.

        Returns list of doc dicts (original, not modified).
        Returns [] if index not built.
        """
        if self._index is None:
            raise RuntimeError("Index not built. Call build() first.")

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores = self._index.get_scores(query_tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append(self._docs[idx])

        return results

    @property
    def build_time_ms(self) -> float:
        return self._build_time_ms

    @property
    def doc_count(self) -> int:
        return len(self._docs)


# ---------------------------------------------------------------------------
# Factory: load from knowledge_base.json
# ---------------------------------------------------------------------------

def load_retriever(kb_path: str | None = None) -> BM25Retriever:
    """
    Load knowledge_base.json and return a built BM25Retriever.
    Default path: ../knowledge-base/knowledge_base.json relative to this file.
    Raises FileNotFoundError if path does not exist.
    """
    if kb_path is None:
        kb_path = os.path.join(
            os.path.dirname(__file__), "..", "knowledge-base", "knowledge_base.json"
        )

    kb_path = os.path.normpath(kb_path)

    if not os.path.exists(kb_path):
        raise FileNotFoundError(f"knowledge_base.json not found at: {kb_path}")

    with open(kb_path, "r", encoding="utf-8") as f:
        docs = json.load(f)

    retriever = BM25Retriever()
    retriever.build(docs)
    return retriever
