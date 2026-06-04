"""
AI2 — Auto STOPWORDS via IDF Threshold
Dùng khi knowledge base scale lên 5k+ docs.
Xem hướng dẫn đầy đủ: ai2/docs/auto_stopwords_formula.md

Cách dùng nhanh:
    from auto_stopwords import compute_auto_stopwords, rebuild_retriever_auto
    retriever = rebuild_retriever_auto(docs, idf_threshold=0.2)
"""

import math
from collections import Counter
from typing import List, Set, Dict, Any

from bm25_module import tokenize, BM25Retriever
from rank_bm25 import BM25Okapi


def compute_auto_stopwords(
    corpus_tokens: List[List[str]],
    idf_threshold: float = 0.2,
) -> Set[str]:
    """
    Tự động tính STOPWORDS dựa trên IDF threshold.

    Công thức:
        IDF(q) = log( (N - df(q) + 0.5) / (df(q) + 0.5) )
        Từ nào có IDF < idf_threshold → stopword tự động.

    Args:
        corpus_tokens:  list of token lists — đầu ra của tokenize() cho từng doc.
        idf_threshold:  ngưỡng IDF để loại từ.
                        Khuyến nghị theo corpus size:
                            250  docs → 0.5  (dùng hard-code vẫn tốt hơn)
                            1k   docs → 0.3
                            5k   docs → 0.2
                            10k+ docs → 0.1

    Returns:
        Set[str] — tập từ nên loại bỏ khi tokenize.
    """
    N = len(corpus_tokens)
    if N == 0:
        return set()

    # Đếm số doc chứa mỗi từ (document frequency)
    df: Counter = Counter()
    for doc_tokens in corpus_tokens:
        for token in set(doc_tokens):   # set() để chỉ đếm 1 lần/doc
            df[token] += 1

    # Lọc theo ngưỡng IDF
    auto_sw: Set[str] = set()
    for token, doc_freq in df.items():
        idf = math.log((N - doc_freq + 0.5) / (doc_freq + 0.5))
        if idf < idf_threshold:
            auto_sw.add(token)

    return auto_sw


def rebuild_retriever_auto(
    docs: List[Dict[str, Any]],
    idf_threshold: float = 0.2,
) -> BM25Retriever:
    """
    Build BM25Retriever dùng auto STOPWORDS thay vì hard-coded.

    Khác với BM25Retriever.build() thông thường:
        - Bước 1: tokenize toàn bộ corpus (dùng hard-coded STOPWORDS cơ bản)
        - Bước 2: tính thêm auto STOPWORDS từ IDF của corpus đó
        - Bước 3: re-tokenize loại bỏ thêm auto STOPWORDS
        - Bước 4: build BM25Okapi trên corpus đã lọc sạch

    QUAN TRỌNG: auto_sw được lưu lại trong retriever._auto_stopwords để
    search() dùng cùng tập từ khi tokenize query — đảm bảo query/index khớp nhau.

    Args:
        docs:           list doc dicts, mỗi doc có {id, title, content, category}
        idf_threshold:  xem compute_auto_stopwords()

    Returns:
        BM25Retriever đã build, có thêm attribute _auto_stopwords
    """
    # Bước 1: tokenize sơ bộ với hard-coded STOPWORDS
    raw_corpus = [
        tokenize(f"{doc.get('title', '')} {doc.get('content', '')}")
        for doc in docs
    ]

    # Bước 2: tính auto stopwords từ corpus thực tế
    auto_sw = compute_auto_stopwords(raw_corpus, idf_threshold)

    # Bước 3: re-tokenize, loại bỏ thêm auto stopwords
    final_corpus = [
        [t for t in tokens if t not in auto_sw]
        for tokens in raw_corpus
    ]

    # Bước 4: build BM25Okapi trực tiếp (bypass BM25Retriever.build() để inject corpus)
    retriever = BM25Retriever()
    retriever._docs = docs
    retriever._index = BM25Okapi(final_corpus)
    retriever._auto_stopwords = auto_sw   # lưu lại để search() dùng

    return retriever


def search_with_auto_stopwords(
    retriever: BM25Retriever,
    query: str,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """
    Search dùng retriever đã build bằng rebuild_retriever_auto().

    Phải dùng hàm này thay vì retriever.search() trực tiếp vì:
        - retriever.search() chỉ dùng hard-coded STOPWORDS khi tokenize query
        - Hàm này bổ sung thêm auto_sw khi tokenize → query/index khớp nhau

    Args:
        retriever:  BM25Retriever từ rebuild_retriever_auto()
        query:      câu truy vấn
        top_k:      số kết quả trả về

    Returns:
        List doc dicts — top_k tài liệu liên quan nhất.
    """
    if retriever._index is None:
        raise RuntimeError("Index not built.")

    # Tokenize query với cả hard-coded và auto stopwords
    auto_sw = getattr(retriever, "_auto_stopwords", set())
    query_tokens = [t for t in tokenize(query) if t not in auto_sw]

    if not query_tokens:
        return []

    scores = retriever._index.get_scores(query_tokens)
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    return [retriever._docs[idx] for idx in top_indices if scores[idx] > 0]


# ---------------------------------------------------------------------------
# Demo / quick test — chạy trực tiếp: python auto_stopwords.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json, os

    kb_path = os.path.join(
        os.path.dirname(__file__), "..", "knowledge-base", "knowledge_base.json"
    )

    print("Loading knowledge base...")
    with open(kb_path, "r", encoding="utf-8") as f:
        docs = json.load(f)

    print(f"Docs loaded: {len(docs)}")

    # Build với auto stopwords
    retriever = rebuild_retriever_auto(docs, idf_threshold=0.2)
    print(f"Auto stopwords found: {len(retriever._auto_stopwords)}")
    print(f"Sample auto stopwords: {sorted(retriever._auto_stopwords)[:20]}")

    # Test search
    results = search_with_auto_stopwords(retriever, "Promise.all parallel fetch", top_k=3)
    print(f"\nQuery: 'Promise.all parallel fetch' → {len(results)} results")
    for r in results:
        print(f"  [{r['category']}] {r['title']}")
