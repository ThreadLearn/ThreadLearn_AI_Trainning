# ThreadLearn AI2 — Race Condition Detection Service

FastAPI microservice phát hiện race condition trong code JavaScript/TypeScript.  
Tích hợp BM25 RAG + LLM, trả kết quả qua REST API.

> **Ghi chú ký hiệu trong tài liệu này:** mọi phần đánh dấu **[SUY LUẬN]** là
> phân tích/đề xuất thêm vào, không có trong code hoặc docs gốc của team —
> phân biệt rõ với phần có trích dẫn `file:line` cụ thể (bằng chứng thật).

---

## Kiến trúc

```
Request → JWT Auth → Redis Cache (hit? return) → BM25 RAG → LLM → MongoDB History → Response
```

| Thành phần | Vai trò | Bắt buộc? |
|---|---|---|
| FastAPI server | Core API | ✅ |
| Redis | Cache kết quả analyze | Không (tắt thì bỏ qua cache) |
| MongoDB | Lưu lịch sử analyze | Không (tắt thì history trả rỗng) |
| LLM provider | Phân tích code thật | Không (dùng `mock` cho dev) |

---

## Cơ chế fix nhiều issue trong 1 lần phân tích

Khi 1 file code chứa **nhiều race-condition pattern cùng lúc** (ví dụ 2-3 vòng
`for` đều dùng `var` + `setTimeout`/`setInterval`), hệ thống không gọi LLM 1
lần duy nhất cho cả file. Đây là quyết định thiết kế quan trọng, rút ra từ 1
bug thực tế gặp phải khi test — ghi lại đây để hiểu rõ lý do và cách team xử
lý, tránh lặp lại sai lầm cũ nếu sau này sửa lại pipeline.

### Vấn đề gốc: 1 LLM call cho cả file thì chỉ sửa được 1 chỗ

**Trước đây:** `rag_pipeline.run()`/`run_streaming()` build 1 prompt chứa toàn
bộ code, gọi LLM 1 lần, rồi gán **cùng 1 kết quả fix** cho mọi issue mà
`race_detector.py` tìm thấy:

```python
# Cách làm CŨ — đã bỏ
llm_output = llm_client.get_llm_fix(code, prompt)   # 1 call cho cả file
for iss in issues:
    iss.fix = fixed_code                             # mọi issue share chung fix
```

**Hệ quả quan sát được:** với code có 3 block lỗi tương tự nhau (setTimeout+var,
setInterval+var, setInterval+let), model Qwen2.5-Coder-1.5B (fine-tune QLoRA,
~700-1000 cặp training) **chỉ sửa đúng block đầu tiên**, bỏ sót 2 block còn
lại — dù cả 3 đều là cùng 1 loại bug. Model 1.5B không đủ khả năng generalize
để sửa nhiều vị trí không liền kề trong 1 lần generate; nó có xu hướng "tập
trung" vào phần đầu prompt.

Kết quả: issue #2, #3 trên UI hiển thị "Suggested rewrite" giống hệt issue #1
(sửa nhầm chỗ, không liên quan gì tới code của chính issue đó) — gây hiểu lầm
nghiêm trọng cho người dùng khi bấm Resolve.

### Giải pháp: mỗi issue có 1 LLM call riêng, dùng `code_snippet` của chính nó

`rag_pipeline._generate_fixes_per_issue()` (trong `rag_pipeline.py`) là nơi xử
lý toàn bộ logic này. Với **N issue phát hiện được** (từ `race_detector.py` →
`report_formatter.format_report()`), mỗi issue nhận **prompt riêng** chỉ chứa
đúng đoạn code liên quan tới nó (`Issue.code_snippet`), không phải toàn file:

```python
for iss in issues:
    snippet = iss.code_snippet                  # chỉ đoạn code của issue này
    snippet_prompt = _build_prompt(snippet, raw_docs)
    fix = llm_client.get_llm_fix(snippet, snippet_prompt)
    iss.fix = fix                                # fix riêng, không share
```

Nhờ vậy model chỉ phải tập trung vào 1 bug pattern tại 1 thời điểm — không còn
tình trạng "chỉ sửa block đầu, bỏ sót phần sau".

### Nếu 2 issue KHÔNG trùng nhau (bug khác vị trí/pattern)

→ **Fix riêng biệt, độc lập.** Mỗi issue gọi LLM 1 lần, ra 1 fix riêng, hiển
thị 1 `IssueCard` riêng trên UI. Đây là trường hợp phổ biến nhất (vd: 1 file
vừa có `closure_loop_var` ở dòng 2-6 vừa có `unhandled_rejection` ở dòng
20-25 — 2 bug hoàn toàn khác nhau, không chồng lấn).

### Nếu 2 issue TRÙNG nhau (cùng chồng lấn 1 đoạn code)

→ **Dedup, chỉ gọi LLM 1 lần, share fix.** Nhiều detector trong
`race_detector.py` có thể match trên **cùng 1 block code** — ví dụ
`_detect_closure_loop_var` (bắt cả for-loop) và `_detect_shared_var_settimeout`
(chỉ bắt phần `setTimeout(...)` bên trong) đều trigger trên cùng đoạn:

```js
for (var i = 0; i < 3; i++) {
  setTimeout(function() {
    console.log(i);
  }, 100);
}
```

→ race detector trả về **2 issue riêng** (`closure_loop_var` line 2-6,
`shared_var_settimeout` line 3-6) dù về bản chất là cùng 1 lỗi nhìn từ 2 góc
detector khác nhau.

Nếu gọi LLM riêng cho từng issue mà không dedup: tốn 2 LLM call (~15-20s mỗi
call) để **ra lại đúng 1 kết quả fix giống hệt nhau**, và UI hiển thị 2
`IssueCard` trùng lặp gây rối mắt, làm người dùng tưởng có 2 bug khác nhau.

**Cách dedup** (`_generate_fixes_per_issue`, biến `snippet_fix_cache`):

1. Với mỗi issue, tính `code_snippet` rồi **mở rộng ngữ cảnh** qua
   `_widen_snippet_for_context()` — xem mục dưới.
2. Dùng snippet đã mở rộng (widened) làm **cache key**. Nếu đã gọi LLM cho
   đúng snippet này rồi (issue trước đó), **dùng lại fix cũ**, không gọi LLM
   lần 2.
3. Checklist tiến trình (`llm_issue_progress` — xem mục Streaming Progress)
   chỉ đếm **số LLM call thực tế**, không đếm số issue — nếu 3 issue dedup còn
   1 call thật, checklist hiện "1/1" chứ không phải "3/3" gây hiểu lầm là còn
   2 bước nữa phải chờ.

```python
snippet_fix_cache: dict[str, str] = {}
for iss in issues:
    widened = _widen_snippet_for_context(full_code, iss.code_snippet, iss.line_range)
    if widened in snippet_fix_cache:
        iss.fix = snippet_fix_cache[widened]        # share fix, KHÔNG gọi LLM
    else:
        iss.fix = llm_client.get_llm_fix(widened, ...)
        snippet_fix_cache[widened] = iss.fix         # cache cho issue trùng sau
```

### Vấn đề phụ: snippet cụt thiếu ngữ cảnh → model sinh code vô nghĩa

Một số detector (điển hình `_detect_shared_var_settimeout`) trả về
`line_range` **bắt đầu ngay tại `setTimeout(...)`**, không bao gồm dòng
`for (var i...)` phía trên khai báo biến `i`. Khi dùng snippet cụt này làm
input LLM, model không biết `i` từ đâu ra — quan sát thực tế cho thấy nó sinh
ra code lặp lại vô nghĩa (3 lần `Promise.all(...)` giống hệt nhau) thay vì 1
fix sạch.

**Giải pháp:** `_widen_snippet_for_context(full_code, snippet, line_range)` —
heuristic tìm identifier nào trong snippet **không có dòng khai báo
(`var`/`let`/`const`) bên trong chính snippet đó**, rồi tìm ngược lên dòng
`for (var|let|const X ...)` gần nhất phía trên khai báo đúng biến đó, mở rộng
snippet để bao gồm luôn dòng đó. Chỉ áp dụng cho **input gửi LLM** — không
đổi phần `code_snippet` hiển thị "Original code" trên UI (vẫn giữ nguyên từ
`report_formatter._extract_snippet`, đúng theo `line_range` detector báo).

### Whole-file fix (fallback) — chỉ gọi khi thực sự cần, không gọi phủ đầu

Có 1 khoảng LLM call thứ 3, gọi trên **toàn bộ file** thay vì 1 snippet, dùng
làm fallback cho 2 trường hợp:

1. Race detector **không tìm thấy issue nào** — vẫn cần trả về ít nhất 1 gợi
   ý cho người dùng, dùng chính fix full-file này làm issue duy nhất.
2. Số issue **vượt quá `_MAX_ISSUES_WITH_OWN_FIX = 5`** — issue thứ 6 trở đi
   không được gọi LLM riêng (tránh vượt `LLM_TIMEOUT_SECONDS = 180s` khi file
   có quá nhiều pattern), dùng lại whole-file fix thay vì bỏ trống.

Ban đầu whole-file fix được gọi **ngay từ đầu, bất kể có cần dùng hay không**
— gây lãng phí ~15-20s ở phần lớn các lần phân tích (≤5 issue, tất cả đều có
`code_snippet` hợp lệ) không bao giờ thực sự dùng đến nó. Đã sửa thành **lazy**
(`_get_full_file_fix()`, cache theo request) — chỉ gọi LLM đúng lúc 1 trong 2
điều kiện trên xảy ra lần đầu tiên, cache kết quả cho các lần dùng lại tiếp
theo trong cùng request (không gọi LLM 2 lần cho cùng 1 whole-file fix).

### Streaming progress — vì sao cần checklist thay vì 1 spinner tĩnh

Vì mỗi issue giờ tốn ~15-20s (1 LLM call riêng), phân tích 1 file có 3-4 issue
độc lập (không dedup được) có thể mất 60-80s ở riêng bước LLM. `run_streaming()`
emit `llm_issue_progress` (`{done, total, current_pattern}`) sau mỗi lần LLM
call thực sự hoàn tất, và `issue_ready` (`{issue: <full data>}`) ngay khi 1
issue có fix xong — để FE (`PipelineProgress.tsx`, `useAnalyzeStream.ts`)
render checklist tick dần từng issue và hiện `IssueCard` ngay khi có, thay vì
người dùng nhìn 1 dòng "LLM Inference" đứng yên hàng chục giây và tưởng ứng
dụng bị treo.

`total` trong `llm_issue_progress` được tính **trước khi chạy**, dựa trên số
snippet unique sau dedup + có cần whole-file hay không — không phải số issue
thô, để checklist phản ánh đúng số bước LLM sẽ thực sự chạy.

---

## Tại sao chọn công nghệ này? (thuật toán / kỹ thuật, so sánh & hướng cải thiện)

Mỗi mục dưới đây trả lời 4 câu cho 1 kỹ thuật cốt lõi của hệ thống: tại sao
chọn nó, nếu dùng kỹ thuật khác thì sao, nếu bỏ hẳn thì hệ quả gì, và có thể
cải thiện bằng gì trong tương lai. Trích dẫn `file:line` là bằng chứng đọc
trực tiếp từ code/docs trong repo — không phải suy đoán.

### 1. BM25 retrieval thay vì vector embedding (`bm25_module.py`)

**Tại sao chọn BM25?**
Ghi rõ trong roadmap (`docs/AI2_TRUNG_ROADMAP.md:138`): *"Tại sao BM25? Nhẹ,
không cần GPU, tốt cho keyword search trên code. Thay cho vector embedding để
tiết kiệm chi phí."* Ràng buộc hiệu năng cụ thể: load time phải < 500ms cho
250 tài liệu (`bm25_module.py:185`).

**Nếu dùng vector embedding (dense search) thay BM25 thì sao?**
Vector embedding được cân nhắc và loại bỏ **ngay từ đầu** vì lý do chi phí/hạ
tầng (cần model embedding chạy encode mỗi query, cần vector index như
FAISS/Qdrant), không phải sau khi thử nghiệm rồi thấy BM25 tốt hơn. Đánh đổi:
BM25 chỉ khớp từ chính xác sau tokenize (miss các từ đồng nghĩa như "block
event loop" vs "blocking synchronous call"), trong khi dense embedding bắt
được similarity ngữ nghĩa nhưng tốn thêm GPU/latency.

**Nếu bỏ hẳn retrieval (không RAG)?**
Có số liệu thực đo trực tiếp (`docs/RESEARCH_LOG.md:24-31`, benchmark 30 case
real-world): model v1 fine-tune không pipeline đạt 63.3% pass, có
BM25+AST pipeline đạt 73.3% — pipeline giúp **+10 điểm phần trăm** cho model
đã fine-tune, nhưng **không giúp gì** cho base model chưa fine-tune (+0 pts)
và giúp rất ít cho GPT-3.5 (+1 pt). Kết luận trong log: *"pipeline khuếch đại
domain knowledge sẵn có, không tạo ra domain knowledge."* Lưu ý quan trọng:
với model v2 (Chain-of-Thought), kết quả **đảo ngược** — không pipeline đạt
76.7%, có pipeline tụt xuống 63.3% — do lỗi prompt format mismatch (xem mục
6), không phải do BM25 tự thân kém.

**Cải thiện tương lai:**
- Cơ chế auto-stopwords dựa IDF **đã có sẵn trong code** (`auto_stopwords.py:19-59`),
  tự kích hoạt khi corpus ≥ 5000 doc (`bm25_module.py:317-325`) — chỉ chưa
  kích hoạt vì corpus hiện tại (~2050 doc) chưa chạm ngưỡng.
- **[SUY LUẬN]** Hybrid search (BM25 + dense embedding qua Qdrant/Pinecone
  hybrid mode) để bắt cả keyword match chính xác lẫn semantic similarity.
- **[SUY LUẬN]** Re-ranking bằng cross-encoder sau BM25 top-k trước khi đưa
  vào prompt.

---

### 2. Regex-based race detector thay vì AST-based static analysis (`race_detector.py`)

**Cây AST là gì, và nó có thực sự được dùng trong hệ thống không?**
AST (Abstract Syntax Tree) là cấu trúc cây biểu diễn code sau khi parser đọc
hiểu cú pháp — mỗi node là 1 thành phần ngôn ngữ thật (ví dụ `ForStatement`,
`CallExpression`, `Identifier`), khác với việc chỉ xem code như text thuần.
Ưu điểm so với regex: AST biết chính xác 1 lệnh `for` bắt đầu/kết thúc ở đâu,
biến nào được khai báo trong scope nào — không phải đoán qua số dòng.

**Có** — AST thật (dùng thư viện `esprima`, tạo ESTree-compatible tree) đã
được tích hợp trong hệ thống, nằm ở `training/modules/ast_preprocessor.py`
(module của AI1 — Ân), cung cấp 3 hàm: `stripComments()` (parse AST, xóa
comment token theo `range`, fallback regex nếu esprima parse lỗi — dòng
34-49), `extractFunctions()` (dùng `esprima.parseScript()` rồi duyệt DFS qua
node tree để tìm `FunctionDeclaration`/`FunctionExpression`/`ArrowFunctionExpression`
— dòng 113-169), và `extract_keywords()` (duyệt token AST, lọc bỏ
`_JS_STOPWORDS`, dùng làm BM25 query — dòng 187-231).

**Nhưng `race_detector.py` chỉ dùng 1 trong 3 hàm đó, và không dùng để detect
pattern.** Import ở dòng 29 lấy cả `extractFunctions, extract_keywords,
stripComments`, nhưng grep thực tế trong file (dòng 678) cho thấy **chỉ
`stripComments()` được gọi** — dùng để xóa comment trước khi quét regex, không
liên quan gì tới việc phát hiện race-condition pattern. `extractFunctions` và
`extract_keywords` được import nhưng không dùng ở đâu trong `race_detector.py`
— import thừa hoặc để dành cho hướng phát triển sau này, không rõ ràng từ
code. Nơi `extract_keywords()` (AST-based) **có khả năng** được dùng là
`rag_pipeline.py` (`_extract_keywords()` gọi `_ast_extract_keywords`), không
phải trong bước detect pattern.

**Nhưng ngay cả ở `rag_pipeline.py`, AST cũng KHÔNG phải đường đi chính** —
nó chỉ là **fallback ưu tiên thấp nhất**, thường không bao giờ được gọi tới
trong thực tế. `_extract_keywords()` (`rag_pipeline.py:37-52`) thử theo thứ
tự: **(1)** `_semantic_keywords()` trước — quét 13 pattern regex cứng định
sẵn trong `_SEMANTIC_PATTERNS` (dòng 56-95, ví dụ pattern "Context Loss" khớp
`setTimeout\s*\(\s*function`); nếu match bất kỳ pattern nào, trả kết quả ngay
và **dừng ở đây, AST không bao giờ được gọi**. **(2)** Chỉ khi không pattern
nào match mới thử AST (`_ast_extract_keywords`). **(3)** Nếu AST cũng lỗi mới
fallback về `tokenize()` (regex thuần trong `bm25_module.py`).

Verify thực tế (chạy trực tiếp `_extract_keywords()` với code mẫu
`for(var i...){setTimeout(...)}`): kết quả trả về là `"context loss bind
arrow this"` — khớp pattern regex "Context Loss" (dòng 84), **không phải**
kết quả AST — dù bug thật của đoạn code này là closure-loop-var, không liên
quan gì tới context loss. Hầu hết code test race-condition điển hình (đúng
nhóm bug mà hệ thống nhắm tới) sẽ khớp 1 trong 13 pattern này ngay từ đầu.
AST chỉ thực sự chạy khi code "lạ", không khớp pattern định sẵn nào — nghĩa
là **trường hợp ít liên quan tới race-condition rõ ràng hơn** mới thật sự đi
qua AST.

Tóm lại: **AST có tồn tại và có chạy thật trong production**, nhưng vai trò
của nó rất hẹp — (a) dọn comment sạch hơn regex thô (`stripComments`, dùng
thật, luôn chạy), và (b) fallback cuối cùng khi cả 13 pattern regex bán-thủ-
công lẫn AST đều không match — trích keyword cho BM25 query. Việc
"phát hiện race condition pattern nào, ở dòng nào, severity gì" (phần lõi
`race_detector.py`) và cả bước chọn category keyword cho BM25 (phần lõi
`_extract_keywords`) **đều ưu tiên regex trước**, AST chỉ là lưới an toàn
phía sau, ít khi thực sự được kích hoạt với input đúng domain bug mà hệ
thống được thiết kế để bắt.

**Tại sao chọn regex quét theo dòng (thay vì tận dụng luôn AST đã có sẵn cho việc detect)?**
Roadmap ghi kế hoạch ban đầu (`docs/AI2_TRUNG_ROADMAP.md:167`): *"Approach:
Rule-based trên AST nodes (không dùng LLM — nhanh, chính xác với patterns rõ
ràng)"*. **Lưu ý khoảng lệch quan trọng:** kế hoạch ghi "AST nodes" nhưng code
thực tế triển khai (`race_detector.py`) hoàn toàn dựa trên regex quét
`_lines()`/`splitlines()`, không parse AST thật — không có comment nào giải
thích tại sao đổi hướng từ kế hoạch sang triển khai thực tế. Đây là khoảng
trống tài liệu cần lưu ý, không phải quyết định có ghi lý do rõ ràng.

**Nếu dùng AST-based (giống AI1) thay vì regex?**
Trong module khác của cùng dự án (`training/LESSONS_LEARNED.md:11`), team tự
ghi nhận: *"Việc áp dụng AST thông qua `@babel/parser` là một bước ngoặt.
Thay vì dùng Regex cắt ghép thủ công, AST giúp bóc tách chính xác cấu trúc
hàm, xóa comment an toàn và chuẩn hóa format."* — team đã tự nhận AST tốt hơn
regex ở AI1 (data preprocessing), nhưng `race_detector.py` của AI2 vẫn chọn
regex thuần, không rõ vì sao không áp dụng cùng nguyên tắc.

Hệ quả kỹ thuật quan sát trực tiếp: detector dùng "window heuristic" (ví dụ
quét 5-10 dòng tiếp theo sau match — `race_detector.py:83,114,267,293`) thay
vì scope thật từ AST — dễ sai khi code format khác thường (dòng quá dài,
logic nằm ngoài window N dòng). Riêng detector `sync_io_blocking` (dòng
462-492) tự bù đắp bằng brace-depth counting (đếm `{`/`}` để mô phỏng scope)
— một dạng "AST giả lập thủ công", cho thấy team tự nhận giới hạn của quét
theo dòng thuần cho ít nhất 1 pattern.

**Nếu bỏ hẳn regex detector (không detect trước khi gọi LLM)?**
Race detector chạy TRƯỚC LLM, dùng để sinh mô tả + severity + `code_snippet`
theo `line_range` cho từng issue. Cơ chế per-issue LLM call (mục "Cơ chế fix
nhiều issue" ở trên) hoàn toàn phụ thuộc dữ liệu này — bỏ detector = luôn rơi
vào nhánh `if not issues: needs_whole_file = True`, mất toàn bộ lợi ích tốc
độ/độ chính xác của việc fix riêng từng issue.

**Cải thiện tương lai:**
- **[SUY LUẬN]** Chuyển sang AST-based thật (dùng `@babel/parser`/`esprima`
  — cùng công cụ `ast_preprocessor.py` của AI1 mà `race_detector.py` đã import
  sẵn ở dòng 29, nhưng chỉ dùng cho keyword extraction chứ chưa dùng để detect
  pattern) để loại bỏ giới hạn "window N dòng" và chính xác scope thật.
- **[SUY LUẬN]** Semgrep hoặc CodeQL cho static analysis chuẩn công nghiệp,
  pattern matching có cấu trúc thay vì regex text.

---

### 3. QLoRA fine-tuning trên Qwen2.5-Coder-1.5B (model, không phải server code)

*(Quyết định của AI1 — Ân, phía training, nhưng ảnh hưởng trực tiếp tới
`llm_client.py` vì server gọi model này qua `local_gpu`/`hf_space` provider.)*

**Tại sao Qwen2.5-Coder-1.5B?**
`training/README.md:12-13`: *"Kích thước siêu nhẹ (3GB), lý tưởng để chạy
Local trên các thiết bị tài nguyên thấp thông qua Ollama/Llama.cpp, nhưng có
năng lực lập trình vượt trội nhờ kiến trúc Qwen2.5."*

**Tại sao QLoRA (không phải full fine-tune hay LoRA fp16 thường)?**
Bằng chứng trực tiếp, đây là quyết định do **ràng buộc phần cứng**, không
phải so sánh lý thuyết (`training/LESSONS_LEARNED.md:14-19`): *"Huấn luyện
mô hình 1.5B tham số trên Kaggle (GPU T4 với 16GB VRAM) liên tục bị Out of
Memory (OOM)... Để tránh OOM, phải tuân thủ nghiêm ngặt kỹ thuật QLoRA
4-bit."* Cấu hình cụ thể: 4-bit NF4 + double_quant, LoRA r=16/alpha=32,
batch_size=1 + gradient_accumulation=8 (thay vì batch lớn hơn — cũng do giới
hạn VRAM T4), fp16 thay vì bf16 vì *"GPU Tesla T4 đời cũ không hỗ trợ kiến
trúc BFloat16 — để mặc định `bf16=True` sẽ gây sập"* (`training/LESSONS_LEARNED.md:18`).

**Nếu dùng full fine-tune hoặc chỉ prompt-engineering (không fine-tune)?**
**[SUY LUẬN]** Full fine-tune cần VRAM cho toàn bộ 1.5B tham số + optimizer
states + gradients — vượt quá 16GB T4 khả dụng, chính là lý do QLoRA được
chọn để tránh OOM. Về prompt-engineering-only: số liệu thực đo cho thấy base
model (chưa fine-tune) chỉ đạt 18.0-60.0% tùy có/không pipeline
(`docs/RESEARCH_LOG.md:24`), thấp hơn nhiều so với Merged v1 fine-tune +
pipeline (73.3%) — domain fine-tuning đóng góp lớn, RAG/prompt engineering
một mình không đủ để đạt chất lượng tương đương.

**Nếu bỏ hẳn fine-tune (chỉ gọi GPT-3.5 qua API)?**
Số liệu thực đo (`docs/RESEARCH_LOG.md:24-29`): GPT-3.5-turbo không pipeline
đạt 61.7%, có pipeline đạt 65.0% — **thấp hơn** Merged v1 (model 1.5B tự
fine-tune) + pipeline đạt 73.3%. Model nhỏ tự fine-tune vượt GPT-3.5-turbo
trên chính benchmark 30-case real-world này.

**Cải thiện tương lai (đã có kế hoạch cụ thể, không phải suy luận):**
- Model v2 dùng thêm Chain-of-Thought (CoT) trong training, đạt 76.7% không
  cần pipeline — cao hơn v1 có pipeline (73.3%). Việc migrate v2 vào
  production đang treo: *"Model v2 chưa migrate vào repo... chưa tích hợp
  rag_pipeline.py"* (`docs/RESEARCH_LOG.md:83-87`).
- Kế hoạch B1 trong `docs/MIGRATION_PLAN_v2.md:60-63`: huấn luyện v3 với
  training data có kèm context RAG mô phỏng sẵn, để model học cách dùng
  context đúng cách ngay từ lúc train thay vì gặp lần đầu lúc inference.

---

### 4. Redis cache theo SHA256(code+language) — exact match, không semantic (`cache.py`)

**Tại sao SHA256 exact-match?**
Docstring giải thích rõ (`cache.py:26-39`): *"SHA256 luôn cho key 64 ký tự cố
định (Redis key có giới hạn độ dài, code có thể rất dài). Collision
probability: 1/2^256 ≈ 0 trong thực tế."* Mục tiêu nghiệp vụ: *"Tránh gọi LLM
2 lần với cùng code → tiết kiệm chi phí + tăng tốc"* (`docs/AI2_TRUNG_ROADMAP.md:245`).
TTL 86400s (24h) vì *"kết quả phân tích không đổi trong 24h nếu code không
đổi"*. Graceful degradation là chủ đích thiết kế: mọi lỗi Redis (`except
Exception: return None/False`) không làm crash server — cache miss thì chạy
pipeline bình thường.

**Nếu dùng semantic cache (embedding + similarity threshold) thay vì exact-match?**
**[SUY LUẬN]** Semantic cache có thể tăng cache hit rate (code chỉ đổi tên
biến vẫn hit), nhưng với race-condition detection — nơi 1 dòng thay đổi nhỏ
(ví dụ thêm `.catch()`) có thể đổi hẳn kết quả phân tích — semantic cache dễ
gây **false cache hit nguy hiểm** (trả kết quả phân tích sai cho code đã sửa
thật sự). SHA256 exact-match tránh hoàn toàn rủi ro này, đánh đổi bằng cache
hit rate thấp hơn.

**Nếu bỏ hẳn cache?**
**[SUY LUẬN]** Mọi request analyze luôn chạy full pipeline (BM25 + tối đa 6
LLM call theo cơ chế per-issue) — không cách nào tránh gọi lại LLM cho cùng 1
đoạn code test đi test lại (rất phổ biến khi user thử/sửa/thử lại code), tăng
chi phí LLM và độ trễ không cần thiết cho end-user.

**Cải thiện tương lai:**
- **[SUY LUẬN]** Cache theo per-issue snippet (không chỉ theo toàn file
  key) — hiện `_generate_fixes_per_issue` đã tự cache theo snippet **trong 1
  request** (`snippet_fix_cache`), nhưng không persist qua Redis giữa các
  request khác nhau. Nếu 2 file khác nhau chứa cùng 1 snippet lỗi phổ biến,
  mỗi request vẫn phải gọi LLM lại từ đầu.

---

### 5. Per-issue LLM call thay vì 1 call cho cả file (`_generate_fixes_per_issue`)

Đã trình bày chi tiết cơ chế ở mục "Cơ chế fix nhiều issue" phía trên. Tóm
tắt lại theo khung 4 câu hỏi:

**Tại sao?** Docstring ghi rõ nguyên nhân gốc (`rag_pipeline.py:206-211`):
model 1.5B fine-tune không đủ khả năng sửa nhiều bug pattern khác nhau cùng
lúc trong 1 lần generate — quan sát thực nghiệm cho thấy nó chỉ sửa đúng
block đầu tiên khi file có 2-3 block lỗi tương tự.

**Nếu dùng 1 call/file với prompt tốt hơn?**
**[SUY LUẬN]** Không có thử nghiệm ghi lại về việc cải thiện prompt để giải
quyết vấn đề này. Nguyên nhân gốc là giới hạn năng lực generate/attention của
model 1.5B khi phải xử lý nhiều task cùng lúc trong 1 lần sinh — cải thiện
prompt có thể giảm nhưng khó chắc chắn giải quyết hoàn toàn.

**Nếu bỏ hẳn per-issue (luôn 1 call/file)?**
Quay lại đúng vấn đề gốc đã ghi trong docstring: model chỉ sửa đúng block đầu
tiên, bỏ sót các block còn lại — không phải suy luận, là hệ quả trực tiếp đã
quan sát trước khi có per-issue.

**Cải thiện tương lai:**
- **[SUY LUẬN]** Batching thông minh hơn: gộp các issue cùng `pattern_id`
  thành 1 LLM call kèm nhiều snippet đánh số, yêu cầu model trả fix theo thứ
  tự — giảm số call trong khi vẫn tránh "chỉ sửa block đầu" nhờ đánh số rõ
  ràng từng block trong cùng 1 prompt.

---

### 6. RAG prompt format — context đặt trước, kết bằng đúng câu training gốc (`_build_prompt`)

Đây là câu chuyện kỹ thuật có bằng chứng mạnh nhất trong toàn hệ thống, vì có
số liệu thực đo + lịch sử lỗi lặp lại.

**Tại sao format này?**
Docstring giải thích chi tiết (`rag_pipeline.py:118-127`): *"Model chỉ được
fine-tune trên format thuần `'Convert to concurrent JavaScript:\n\n{code}\n'`
— không hề thấy context RAG lúc train. Nhồi context bằng cú pháp lạ (vd thẻ
`<reference_docs>`) khiến input rơi ra ngoài phân phối huấn luyện và model có
xu hướng chỉ echo lại code gốc thay vì sinh fix."* Format đúng: context đặt
TRƯỚC, kết thúc luôn bằng đúng câu lệnh training gốc để model nhận diện điểm
bắt đầu completion.

**Bằng chứng hậu quả khi format sai (đã xảy ra thật, 2 lần):**
- Lần 1 (model v1): lệch eval/train format làm rớt từ **70% xuống 35%**
  (`training/LESSONS_LEARNED.md`, dẫn lại trong `docs/RESEARCH_LOG.md:65`).
- Lần 2 (model v2): `docs/RESEARCH_LOG.md:67-73` liệt kê **3 format từng tồn
  tại song song trong codebase** — training gốc (không context), production
  `rag_pipeline.py` (tiếng Việt, "Tài liệu {i}"), và notebook eval riêng
  (tiếng Anh, "Reference {i}", cắt 500 ký tự). Model v2 (CoT) một mình đạt
  76.7%, nhưng qua format notebook tự chế thì tụt xuống 63.3% — model *"echo
  lại nguyên văn đoạn context retrieved thay vì áp dụng vào bug thực tế"*
  (`docs/RESEARCH_LOG.md:63`), có ví dụ log cụ thể minh họa (case `rw_04`).

**Nếu dùng format khác (context sau code, hoặc tiếng Anh, hoặc cắt ngắn)?**
Đã thử và đo được: bất kỳ format nào khác đúng training format đều gây tụt
điểm nghiêm trọng (35-63% thay vì 70-77%) — không phải giả thuyết, là số liệu
thực đo lặp lại 2 lần độc lập trên 2 phiên bản model khác nhau.

**Nếu bỏ hẳn context injection (không RAG trong prompt)?**
`docs/MIGRATION_PLAN_v2.md:65-70` đã đề xuất cụ thể: với model v2, bỏ RAG
hoàn toàn (route riêng theo `MODEL_VERSION`), vì v2 không pipeline (76.7%) đã
vượt v1+pipeline (73.3%). Rủi ro đã ghi rõ: chưa rõ RAG có giúp các category
còn yếu của v2 hay không (Race Condition, Zalgo, Stream Leak — mỗi loại mới
đạt 50% theo `docs/RESEARCH_LOG.md`).

**Cải thiện tương lai (kế hoạch cụ thể đã ghi trong `docs/MIGRATION_PLAN_v2.md`):**
- Phương án A (dòng 48-54): nếu format `_build_prompt()` thật (production)
  cứu được pipeline cho v2, chốt nó làm chuẩn duy nhất, xóa các bản
  `build_prompt()` trùng lặp trong notebook.
- Phương án B1 (dòng 60-63): train lại v3 với dataset có context RAG mô
  phỏng ngay trong lúc training (dùng BM25 hiện có để mô phỏng đúng input
  production) — để model học cách dùng context thay vì gặp lần đầu lúc
  inference.
- Đồng bộ 1 nguồn duy nhất cho hàm build prompt (dòng 81): notebook import
  trực tiếp file `.py` thay vì copy tay, tránh lặp lại lỗi 3-format-khác-nhau.

---

## Yêu cầu

- Python 3.13+
- (Tùy chọn) Redis, MongoDB, Docker

---

## Chạy local (dev)

### Bước 1 — Cài dependencies

```bash
cd ThreadLearn-AI-Trainning/server/server
pip install -r requirements.txt
```

### Bước 2 — Tạo file `.env`

Tạo file `server/server/.env` với nội dung sau (copy và điền giá trị):

```env
# Chọn 1: mock | openai | ollama
# - mock   → dev/test, không cần key, trả Issue cứng
# - openai → cần OPENAI_API_KEY
# - ollama → cần Ollama chạy local
LLM_PROVIDER=mock

OPENAI_API_KEY=

# Phải khớp với JWT_SECRET trong Node.js backend
# Để trống hoặc giữ nguyên khi test local
JWT_SECRET=your_super_secret_access_key_change_me

# Tùy chọn — server chạy bình thường nếu thiếu
REDIS_URL=redis://localhost:6379
MONGODB_URL=mongodb://localhost:27017
OLLAMA_URL=http://localhost:11434
HF_TOKEN=
```

> ⚠️ **Không commit file `.env` lên git.** File đã có trong `.gitignore`.

### Bước 3 — Chạy server

```bash
cd ThreadLearn-AI-Trainning/server/server
python -m uvicorn main:app --reload --port 8001
```

Kiểm tra server hoạt động:

```bash
curl http://localhost:8001/health
# → {"status":"ok","retriever_docs":2050}
```

Swagger UI: http://localhost:8001/docs

---

## Chạy với Docker

```bash
cd ThreadLearn-AI-Trainning/server

# Build image
docker build -t threadlearn-server .

# Chạy với env vars
docker run -d \
  -p 8001:8001 \
  -e LLM_PROVIDER=mock \
  -e JWT_SECRET=your_super_secret_access_key_change_me \
  --name server \
  threadlearn-server
```

Kiểm tra:

```bash
curl http://localhost:8001/health
```

---

## API Endpoints

### `GET /health` — Public, không cần token

```bash
curl http://localhost:8001/health
```

```json
{
  "status": "ok",
  "retriever_docs": 2050
}
```

---

### `POST /api/v1/ai/analyze` — Yêu cầu JWT

**Request:**

```bash
curl -X POST http://localhost:8001/api/v1/ai/analyze \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "for(var i=0;i<3;i++){setTimeout(function(){console.log(i)},1000);}",
    "language": "javascript",
    "user_id": "user-123"
  }'
```

**Response:**

```json
{
  "user_id": "user-123",
  "language": "javascript",
  "issues": [
    {
      "line_range": "1",
      "severity": "high",
      "description": "Closure loop variable — biến i dùng var, tất cả callback share cùng reference.",
      "fix": "Thay var bằng let để tạo block scope mới mỗi iteration."
    }
  ],
  "docs_used": ["Closure Loop Variable", "var vs let Scope"],
  "cached": false
}
```

| Field | Giá trị |
|---|---|
| `severity` | `"high"` / `"medium"` / `"low"` |
| `cached` | `true` nếu lấy từ Redis, `false` nếu gọi LLM mới |

---

### `GET /api/v1/ai/history/{user_id}` — Yêu cầu JWT

```bash
curl "http://localhost:8001/api/v1/ai/history/user-123?page=1&limit=20" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

```json
{
  "user_id": "user-123",
  "total": 5,
  "page": 1,
  "limit": 20,
  "records": [ ... ]
}
```

> Chỉ xem được history của chính mình — AI2 so sánh `user_id` trong JWT với param.

---

## Tích hợp từ Node.js Backend

### Tạo JWT

JWT phải được ký với cùng `JWT_SECRET` trong `server/server/.env`.

```javascript
import jwt from 'jsonwebtoken';

const token = jwt.sign(
  { sub: userId, exp: Math.floor(Date.now() / 1000) + 3600 },
  process.env.JWT_SECRET,
  { algorithm: 'HS256' }
);
```

### Gọi AI2

```javascript
const response = await fetch('http://localhost:8001/api/v1/ai/analyze', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    code: userCode,
    language: 'javascript',
    user_id: userId,
  }),
});

const result = await response.json();
// result.issues[] — danh sách lỗi phát hiện được
```

---

## Chọn LLM Provider

| Provider | Cấu hình | Độ chính xác |
|---|---|---|
| `mock` | Không cần gì | Dev/demo only — trả Issue cứng |
| `openai` | `OPENAI_API_KEY=sk-...` | Cao nhất |
| `ollama` | Ollama chạy local + `OLLAMA_URL` | Trung bình, offline |

Đổi provider: sửa `LLM_PROVIDER` trong `server/server/.env` rồi restart server.

---

## Tích hợp Redis & MongoDB (tùy chọn)

Nếu không có, server vẫn chạy bình thường — chỉ mất cache và history.

**Chạy nhanh bằng Docker:**

```bash
docker run -d -p 6379:6379 redis:alpine
docker run -d -p 27017:27017 mongo:7
```

---

## Chạy Tests

Từ thư mục gốc repo (`WDP-Code/`):

```bash
cd ThreadLearn-AI-Trainning/server/server
python -m pytest ../tests/ -v
```

---

## Giới hạn

| Giới hạn | Giá trị |
|---|---|
| Concurrent LLM calls | 3 (queue nếu vượt) |
| Timeout mỗi request | 30 giây |
| History per page | Tối đa 100 |
| Code input | 512 KB |
