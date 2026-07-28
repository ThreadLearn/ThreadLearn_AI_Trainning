# Script thuyết trình — Slide "Workflow" (RAG pipeline ThreadLearn)

Dựa trên code thật: `server/server/rag_pipeline.py` (hàm `run_streaming`, `_extract_keywords`, `_semantic_keywords`, `_generate_fixes_per_issue`).

---

## Mở đầu (10s)

"Slide này mô tả toàn bộ workflow xử lý 1 request từ lúc người dùng nộp code tới lúc trả về Issue Card kèm fix. Đây là luồng chạy thật trong `rag_pipeline.py`, không phải sơ đồ khái niệm."

---

## Bước 1-2: Input → Race Detector (15s)

"Code người dùng nộp vào trước tiên qua **Race Detector** — quét bằng regex pattern, có bước `stripComments` để loại bỏ comment tránh false positive. Đây là bước rẻ, chạy trước LLM để nhanh chóng biết có bao nhiêu issue và severity của từng issue."

---

## Bước 3: Keyword Extraction — 3 tầng ưu tiên (45s, phần trọng tâm)

"Đây là phần hay bị hiểu nhầm nhất — 3 tầng **KHÔNG chạy song song, mà chạy tuần tự có điều kiện dừng sớm**. Code thật trong hàm `_extract_keywords`:

```python
def _extract_keywords(code):
    semantic = _semantic_keywords(code)      # 3a
    if semantic:
        return semantic                       # dừng ở đây nếu match
    if _HAS_AST:
        kw = _ast_extract_keywords(code)      # 3b — chỉ chạy nếu 3a rỗng
        if kw.strip():
            return kw
    return tokenize(code)[:20]                 # 3c — chỉ chạy nếu cả 3a và 3b đều rỗng
```

**3a. SEMANTIC PATTERN MATCH (13 Regex Rules, Priority 1)**
Đây là tầng chạy trước tiên. Có đúng 13 cặp `(regex, keywords)` hard-code sẵn trong `_SEMANTIC_PATTERNS`, mỗi cặp bắt 1 loại bug cụ thể: Double Callback, Zalgo, Sequential Awaits, Unhandled Rejection, Event Loop Blocking, Resource Exhaustion, Stream Leak, Context Loss, Race Condition (file system + shared state), Callback Hell. Nếu code khớp bất kỳ regex nào trong 13 rule này, hàm trả về ngay bộ từ khóa gắn sẵn cho pattern đó — ví dụ code có `await` 2 lần liên tiếp không `Promise.all` sẽ trả về chuỗi `'sequential await Promise.all parallel concurrent'`.

**3b. AST FALLBACK (Esprima Parse, Priority 2, chỉ chạy nếu 3a rỗng)**
Nếu không regex nào ở 3a khớp, hệ thống mới parse code thành AST bằng Esprima (thư viện từ AI1), duyệt cây lấy Identifier token, để trích từ khóa tổng quát hơn. Bước này tốn công hơn 3a (phải parse cú pháp thật) nên chỉ chạy khi 3a thất bại.

**3c. PLAIN TOKENIZE (Priority 3, fallback cuối)**
Nếu cả AST cũng import lỗi hoặc trả rỗng, hệ thống tokenize thô bằng `bm25_module.tokenize()` — cùng hàm dùng để build index — lấy 20 token đầu làm query. Đây là lưới an toàn cuối, đảm bảo luôn có query để search dù 2 tầng trên thất bại.

**Vì sao thứ tự này quan trọng — dòng chữ "AST hiếm khi thực sự chạy":**
13 regex rule ở 3a được viết để bắt trúng phần lớn pattern race-condition phổ biến trong benchmark thực tế. Vì vậy trong đa số request, 3a đã trả về kết quả và hàm return ngay — 3b (AST) gần như không bao giờ được gọi tới trên dữ liệu thật. AST chỉ đóng vai trò dự phòng cho code có cấu trúc lạ, không khớp regex nào."

### Ví dụ thật — BM25 nhận được gì khác nhau ở mỗi tầng

"Để thấy rõ 3 tầng cho ra input khác chất hoàn toàn cho BM25, xét 3 case cụ thể:

**Case A — 3a match, dừng ngay:**
```js
async function loadDashboard(userId) {
  const profile = await fetch(`/api/profile/${userId}`).then(r => r.json());
  const orders = await fetch(`/api/orders/${userId}`).then(r => r.json());
  return { profile, orders };
}
```
Regex `sequential_awaits` trong `_SEMANTIC_PATTERNS` khớp ngay (2 `await` liền dòng, không `Promise.all`). Hàm trả về thẳng:
```
query = "sequential await Promise.all parallel concurrent"
```
BM25 nhận 5 từ **cố định, hard-code sẵn** — không liên quan gì tới code thật (không có `profile`, `userId`, `fetch`), chỉ là nhãn khái niệm khớp thẳng title tài liệu trong KB. 3b và 3c không chạy.

**Case B — 3a rỗng, rơi xuống 3b (AST):**
```js
class InventoryManager {
  syncWarehouse(items) {
    return items.reduce((acc, x) => acc.merge(x), this.baseStock);
  }
}
```
Không khớp regex nào trong 13 rule (không `for var`, không 2 `await`, không `setTimeout`...) → `_semantic_keywords()` trả `""`. Rơi xuống `_ast_extract_keywords()`: esprima parse thật, duyệt token type `Identifier`, loại stopword (`class`, `return`, `this`...):
```
query = "InventoryManager syncWarehouse items reduce acc x merge baseStock"
```
BM25 nhận **token thật lấy trực tiếp từ code**, giữ nguyên dạng gốc (kể cả CamelCase), theo đúng thứ tự xuất hiện — khác hẳn case A vì đây là keyword cụ thể của bài toán, không phải nhãn cố định.

**Case C — cả 3a lẫn 3b đều rỗng, rơi xuống 3c (tokenize thô):**
Trường hợp hiếm: esprima import lỗi (`_HAS_AST = False`) hoặc parse thất bại êm, trả `kw.strip() == ""`. Rơi xuống `bm25_module.tokenize(code)[:20]` — cùng hàm dùng để build index lúc server khởi động, nhưng dùng bộ `STOPWORDS` khác với AST và có bước tách CamelCase/snake_case. Cùng code case B, nếu esprima fail:
```
query = "inventory manager sync warehouse items reduce acc merge base stock"
```
Khác case B ở chỗ `InventoryManager` bị tách thành 2 token `inventory manager` thay vì giữ nguyên 1 token — vì dùng tokenizer hoàn toàn khác với AST.

**Tóm gọn 3 kiểu input mà BM25 nhận được:**

| Tầng | BM25 nhận được | Nguồn |
|---|---|---|
| 3a | Cụm từ khái niệm cố định, hard-code sẵn theo pattern | Bảng tra `_SEMANTIC_PATTERNS`, không liên quan code |
| 3b | Identifier thật trong code, giữ nguyên dạng (CamelCase) | Duyệt AST thật của esprima |
| 3c | Token thật nhưng đã tách CamelCase/snake_case | Regex split đơn giản trong `bm25_module.tokenize()` |

Nói cách khác: 3a cho BM25 một *nhãn khái niệm* để tìm tài liệu đúng chủ đề bug; 3b và 3c cho BM25 *từ vựng thật của code* để tìm tài liệu theo API/tên hàm cụ thể — hai chiến lược search khác hẳn nhau, và hệ thống ưu tiên chiến lược nhãn khái niệm trước vì nó chính xác hơn cho các bug pattern đã biết."

---

## Bước 4-5: BM25 Search → Prompt Builder (20s)

"Từ khóa ở bước 3 (dù đến từ 3a, 3b hay 3c) được đưa vào BM25 search trên knowledge base — retriever trả về top-1 tài liệu liên quan nhất (`top_k=1` trong code). Prompt Builder ghép tài liệu đó với code gốc thành 1 prompt hoàn chỉnh theo đúng format completion mà model đã fine-tune, đặt context TRƯỚC code để không lệch khỏi phân phối lúc training."

---

## Bước 6: Per-Issue LLM Fix Loop (30s)

"Đây là phần có icon mũi tên xoay tròn trong slide — với chú thích '1 LLM call / issue, không phải 1 call / file'. Lý do: model Qwen2.5-Coder-1.5B fine-tune bằng QLoRA không đủ khả năng sửa nhiều bug pattern khác nhau trong 1 lần generate. Nếu file có 3 vòng lặp lỗi tương tự, gọi LLM 1 lần cho cả file thì model chỉ sửa đúng block đầu tiên, bỏ sót các block còn lại.

Giải pháp: gọi LLM riêng cho từng issue, dùng đúng `code_snippet` của issue đó — tối đa 5 issue tự sửa riêng (`_MAX_ISSUES_WITH_OWN_FIX = 5`), có dedup theo snippet trùng nhau để không lãng phí LLM call, và có cache lazy cho fix full-file (chỉ gọi khi thật sự cần, không gọi phủ đầu)."

---

## Bước 7-8: Stream Events → Output (15s)

"Mỗi bước hoàn tất, `emit()` phát event `step` báo trạng thái running/done ra frontend theo thời gian thực. Riêng bước LLM fix, mỗi issue xong sẽ phát thêm event `issue_ready` — để FE hiển thị Issue Card đó ngay lập tức thay vì đợi toàn bộ pipeline chạy xong mới hiện tất cả cùng lúc, giúp trải nghiệm mượt hơn khi có nhiều issue (mỗi issue mất 15-20s do gọi LLM riêng)."

---

## Kết (10s)

"Tóm lại: workflow này tối ưu theo nguyên tắc 'rẻ trước, đắt sau' — regex rẻ nhất chạy trước (3a), AST đắt hơn chỉ chạy khi cần (3b), và LLM đắt nhất chỉ gọi đúng số lần cần thiết, theo từng issue thay vì cả file."
