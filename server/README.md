# ThreadLearn AI2 — Race Condition Detection Service

FastAPI microservice phát hiện race condition trong code JavaScript/TypeScript.  
Tích hợp BM25 RAG + LLM, trả kết quả qua REST API.

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
