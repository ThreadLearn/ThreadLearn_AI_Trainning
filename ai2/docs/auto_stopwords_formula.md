# Auto STOPWORDS via IDF Threshold

Tài liệu này ghi lại công thức và code mẫu để **tự động tính STOPWORDS**
khi knowledge base scale lên lớn (khuyến nghị: 5k+ docs).

Hiện tại `bm25_module.py` dùng hard-coded STOPWORDS — xem comment trong file đó
để biết khi nào nên chuyển sang cách này.

---

## Tại sao IDF có thể thay thế STOPWORDS?

BM25 tính điểm mỗi từ `q` trong tài liệu `D`:

```
score(q, D) = IDF(q) × TF_normalized(q, D)
```

Trong đó IDF (Inverse Document Frequency):

```
IDF(q) = log( (N - df(q) + 0.5) / (df(q) + 0.5) )

Ký hiệu:
  N     = tổng số tài liệu trong corpus
  df(q) = số tài liệu chứa từ q (document frequency)
```

**Khi từ xuất hiện trong quá nhiều doc:**
- df(q) → N  →  IDF(q) → log(0.5 / N) ≈ 0 (hoặc âm)
- Đóng góp điểm của từ đó ≈ 0 → BM25 tự bỏ qua

→ Nếu corpus đủ lớn, STOPWORDS hard-code là thừa.

---

## Công thức tính ngưỡng (threshold)

```
Một từ là "stopword tự động" khi:
  IDF(q) < threshold

Gợi ý threshold theo corpus size:
  250  docs → threshold = 0.5   (conservative, dùng hard-code vẫn tốt hơn)
  1k   docs → threshold = 0.3
  5k   docs → threshold = 0.2
  10k+ docs → threshold = 0.1   (BM25 đủ mạnh, bỏ STOPWORDS hoàn toàn)
```

---

## Code mẫu — thay thế hard-coded STOPWORDS

```python
import math
from collections import Counter
from typing import List, Set


def compute_auto_stopwords(
    corpus_tokens: List[List[str]],
    idf_threshold: float = 0.2,
) -> Set[str]:
    """
    Tự động tính STOPWORDS dựa trên IDF threshold.

    Args:
        corpus_tokens:  list of token lists (đầu ra của tokenize() cho từng doc)
        idf_threshold:  từ có IDF < threshold → coi là stopword
                        Khuyến nghị: 0.2 cho corpus 5k+ docs

    Returns:
        Set[str] — tập từ nên loại bỏ khi tokenize query

    Ví dụ:
        corpus = [tokenize(doc["title"] + " " + doc["content"]) for doc in docs]
        auto_sw = compute_auto_stopwords(corpus, idf_threshold=0.2)
    """
    N = len(corpus_tokens)
    if N == 0:
        return set()

    # Đếm số doc chứa mỗi từ (df)
    df: Counter = Counter()
    for doc_tokens in corpus_tokens:
        for token in set(doc_tokens):   # set() để chỉ đếm 1 lần/doc
            df[token] += 1

    # Tính IDF và lọc theo threshold
    stopwords: Set[str] = set()
    for token, doc_freq in df.items():
        idf = math.log((N - doc_freq + 0.5) / (doc_freq + 0.5))
        if idf < idf_threshold:
            stopwords.add(token)

    return stopwords
```

---

## Cách tích hợp vào bm25_module.py khi scale

Thay thế đoạn build trong `BM25Retriever.build()`:

```python
def build(self, docs, idf_threshold: float = 0.2):
    self._docs = docs
    corpus = [tokenize(f"{d.get('title','')} {d.get('content','')}") for d in docs]

    # Tính auto stopwords từ corpus thực tế
    auto_sw = compute_auto_stopwords(corpus, idf_threshold)

    # Re-tokenize với auto stopwords bổ sung
    final_corpus = [
        [t for t in tokens if t not in auto_sw]
        for tokens in corpus
    ]

    self._index = BM25Okapi(final_corpus)
```

> **Lưu ý:** Khi dùng auto stopwords, phải lọc query bằng cùng tập `auto_sw`
> trong `search()`, nếu không query và index sẽ không khớp nhau.

---

## Khi nào nên chuyển?

| Điều kiện | Hành động |
|-----------|-----------|
| KB < 5k docs | Giữ hard-coded STOPWORDS trong `bm25_module.py` |
| KB 5k–10k docs | Dùng `compute_auto_stopwords` với `threshold=0.2`, giữ hard-coded làm fallback |
| KB > 10k docs | Bỏ hoàn toàn hard-coded, chỉ dùng auto + BM25 IDF tự nhiên |
| Thêm ngôn ngữ mới (Python, Java...) | Bắt buộc dùng auto — hard-coded không scale đa ngôn ngữ |
