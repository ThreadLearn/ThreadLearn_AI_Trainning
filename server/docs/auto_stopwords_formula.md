# Auto STOPWORDS via IDF Threshold

Tài liệu này ghi lại công thức và hướng dẫn dùng **auto STOPWORDS**
khi knowledge base scale lên lớn (khuyến nghị: 5k+ docs).

**File implementation:** `server/server/auto_stopwords.py`
— chứa code sẵn sàng dùng, không cần viết lại.

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

## Cách dùng — file `server/server/auto_stopwords.py`

File này chứa 3 hàm sẵn sàng dùng:

### 1. `compute_auto_stopwords(corpus_tokens, idf_threshold)`
Tính tập STOPWORDS tự động từ corpus.

```python
from auto_stopwords import compute_auto_stopwords
from bm25_module import tokenize

corpus = [tokenize(f"{doc['title']} {doc['content']}") for doc in docs]
auto_sw = compute_auto_stopwords(corpus, idf_threshold=0.2)
print(auto_sw)  # {"use", "call", "run", ...}
```

### 2. `rebuild_retriever_auto(docs, idf_threshold)` ← hàm chính
Thay thế toàn bộ `load_retriever()` khi scale.

```python
from auto_stopwords import rebuild_retriever_auto, search_with_auto_stopwords

# Thay load_retriever() bằng dòng này
retriever = rebuild_retriever_auto(docs, idf_threshold=0.2)
```

### 3. `search_with_auto_stopwords(retriever, query, top_k)`
Phải dùng hàm này thay vì `retriever.search()` — vì query cần lọc cùng tập auto_sw.

```python
results = search_with_auto_stopwords(retriever, "Promise.all parallel fetch", top_k=3)
```

> **Lưu ý quan trọng:** Không dùng `retriever.search()` trực tiếp sau `rebuild_retriever_auto()`.
> Query phải lọc cùng tập `auto_sw`, nếu không query/index sẽ không khớp nhau.

### Quick test

```bash
cd server/server
python auto_stopwords.py
```

---

## Khi nào nên chuyển?

| Điều kiện | Hành động |
|-----------|-----------|
| KB < 5k docs | Giữ hard-coded STOPWORDS trong `bm25_module.py` |
| KB 5k–10k docs | Dùng `compute_auto_stopwords` với `threshold=0.2`, giữ hard-coded làm fallback |
| KB > 10k docs | Bỏ hoàn toàn hard-coded, chỉ dùng auto + BM25 IDF tự nhiên |
| Thêm ngôn ngữ mới (Python, Java...) | Bắt buộc dùng auto — hard-coded không scale đa ngôn ngữ |
