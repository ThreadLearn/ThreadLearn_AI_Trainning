# AI2 — Trung: Roadmap & Định hướng thực hiện

> ⚠️ **SNAPSHOT LỊCH SỬ — roadmap giai đoạn đầu, một số số liệu đã lỗi thời** (ví dụ knowledge base 250 docs, detector 10-pattern JS+Python). Hệ thống cuối cùng: knowledge base 2,050 docs, detector 5-pattern JS-only. Số liệu hiện hành: [`docs/RESEARCH_LOG.md`](RESEARCH_LOG.md).

## 1. Tổng quan vai trò

Mình là **AI Engineer 2** — phụ trách phần **Serving, RAG & Race Condition**.

Nói đơn giản: AI1 (Ân) train ra con model, mình xây toàn bộ hệ thống để **nhận code từ user → phân tích → trả kết quả** thông minh về cách đa luồng hóa.

---

## 2. Kiến trúc tổng thể (mình phụ trách)

```
Frontend (React)
      │
      │  POST /api/v1/ai/analyze  {code, language}
      ▼
[Node.js Backend] ──── verify JWT ────►
      │
      │  forward request
      ▼
[FastAPI Server — AI2]
      │
      ├─► Redis Cache? ──── HIT ────► return cached result
      │        │
      │       MISS
      │        │
      ▼        ▼
[AST Preprocessor]  ← module từ AI1 (ast_preprocessor.py)
      │
      ├─► Extract keywords từ AST
      │
      ▼
[BM25 Search] ──► top 3 docs từ Knowledge Base (250+ docs)
      │
      ▼
[Build Prompt] = code + context docs + instruction
      │
      ├─► Iter 2-3: gọi OpenAI GPT-3.5 (tạm)
      ├─► Iter 3+:  gọi Ollama (model fine-tune của AI1)
      │
      ▼
[Output Parser] ← module từ AI1 (output_parser.py)
      │
      ├─► suggestions JSON
      │
      ├─► [Race Condition Detector] ──► warnings JSON
      │
      ▼
[Merge kết quả] ──► save MongoDB ──► set Redis Cache
      │
      ▼
Response JSON → Frontend
```

---

## 3. Luồng dữ liệu chi tiết — Request /analyze

### Input (từ Frontend)
```json
{
  "code": "function fetchAll() { ... }",
  "language": "javascript",
  "user_id": "abc123"
}
```

### Xử lý từng bước
1. **JWT verify** — middleware check token từ Node.js
2. **Redis check** — SHA256(code + language) → có cache → trả luôn
3. **AST parse** — gọi module AI1 → lấy cấu trúc code
4. **BM25 search** — extract keywords từ AST → tìm 3 docs liên quan nhất trong knowledge base
5. **Build prompt** — ghép code + 3 docs + instruction vào prompt
6. **LLM call** — GPT-3.5 hoặc Ollama → trả suggestions
7. **Race condition detect** — scan AST nodes theo 10 rule patterns
8. **Format output** — chuẩn hóa JSON response
9. **Save MongoDB** — lưu lịch sử analysis của user
10. **Set Redis** — cache kết quả 24h

### Output (trả về Frontend)
```json
{
  "suggestions": [
    {
      "type": "parallel",
      "description": "Dùng Promise.all thay vì sequential await",
      "code_before": "...",
      "code_after": "..."
    }
  ],
  "race_conditions": [
    {
      "line_range": [12, 15],
      "severity": "high",
      "description": "Shared variable modified in setTimeout without lock",
      "fix": "Dùng async/await hoặc mutex pattern"
    }
  ],
  "cached": false,
  "tokens_used": 420
}
```

---

## 4. Lộ trình 8 tuần — Chi tiết từng task

### ITER 1 (Tuần 1-2): Nền tảng dữ liệu & Phân tích

#### AI2-01 — Knowledge Base (W1)
**Mục tiêu:** 250+ tài liệu về concurrent patterns JS/Python

**Nội dung cần thu thập:**
- JS patterns: `Promise.all`, `Promise.race`, `Worker threads`, `async/await`, `EventEmitter`, `Mutex/Semaphore`
- Python patterns: `asyncio`, `threading.Lock`, `multiprocessing`, `concurrent.futures`, `Queue`
- Anti-patterns: callback hell, blocking in async, shared state
- Race condition examples: shared var + setTimeout, no-lock shared list

**Format mỗi document:**
```json
{
  "id": "js-001",
  "title": "Promise.all for parallel execution",
  "content": "...",
  "language": "javascript",
  "category": "patterns"
}
```

**Output:** `knowledge_base.json` — 250+ docs, 4 categories

---

#### AI2-02 — BM25 Indexing Module (W1-2)
**Mục tiêu:** Module tìm kiếm relevant docs dựa trên code user gửi lên

**Tại sao BM25?** Nhẹ, không cần GPU, tốt cho keyword search trên code. Thay cho vector embedding để tiết kiệm chi phí.

**Cách hoạt động:**
1. `buildIndex(docs)` — tokenize và index toàn bộ 250 docs khi server khởi động
2. `search(query, topK=3)` — nhận keywords từ AST, trả 3 docs phù hợp nhất
3. Load time < 500ms (index load vào RAM khi start)

**Output:** `bm25_module.py` + index file

---

#### AI2-03 — Race Condition Detector (W2)
**Mục tiêu:** Phát hiện 10 loại race condition phổ biến trong JS/Python

**10 patterns cần detect:**

| # | Pattern | Ngôn ngữ |
|---|---------|----------|
| 1 | Shared var modified in setTimeout | JS |
| 2 | Promise without await (fire-and-forget) | JS |
| 3 | Concurrent write to same array/object | JS |
| 4 | Closure capturing mutable loop var | JS |
| 5 | Global variable in thread function | Python |
| 6 | Shared list/dict without Lock | Python |
| 7 | Thread reading while other writes | Python |
| 8 | Missing join() before using result | Python |
| 9 | Singleton with lazy init in threads | JS/Python |
| 10 | Counter increment without atomic op | JS/Python |

**Approach:** Rule-based trên AST nodes (không dùng LLM — nhanh, chính xác với patterns rõ ràng)

**Output:** `race_detector.py` — detect ≥12/15 test cases, FP < 2/10

---

#### AI2-04 — Report Formatter (W2)
**Mục tiêu:** Chuẩn hóa output của race detector thành JSON đẹp

**Schema output:**
```json
[
  {
    "line_range": [10, 15],
    "severity": "high",
    "description": "...",
    "fix": "..."
  }
]
```

**Severity rules:**
- `high`: race condition xảy ra deterministic, luôn crash
- `medium`: race condition xảy ra theo timing, có thể tái hiện
- `low`: potential issue, ít khả năng xảy ra

---

### ITER 2 (Tuần 3-4): Server & Pipeline OpenAI

#### AI2-05 — FastAPI Server (W3)
**Mục tiêu:** Server AI độc lập, giao tiếp với Node.js backend qua HTTP

**Tại sao FastAPI (Python) thay vì Express (JS)?**
- AI libraries (transformers, torch, langchain) đều Python-native
- Async support tốt hơn cho LLM calls
- Pydantic validation built-in

**Routes:**
```
POST /api/v1/ai/analyze      — main endpoint
GET  /api/v1/ai/history/{id} — lịch sử analysis
GET  /health                 — health check cho Docker
```

**Middleware JWT:** Node.js ký JWT → FastAPI verify bằng cùng secret

---

#### AI2-06 — RAG Pipeline với OpenAI (W3-4)
**Đây là task cốt lõi nhất của Iter 2.**

**RAG = Retrieval Augmented Generation:**
- Thay vì hỏi LLM "hãy suggest cách đa luồng hóa code này"
- Mình hỏi: "dựa trên [3 docs relevant nhất] này, hãy suggest cách đa luồng hóa code này"
- Kết quả tốt hơn nhiều vì LLM có context cụ thể

**Prompt template:**
```
You are a concurrent programming expert.

RELEVANT PATTERNS:
{doc_1_content}
{doc_2_content}
{doc_3_content}

TASK: Analyze this {language} code and suggest how to make it concurrent:
{user_code}

Return JSON with keys: suggestions (array), explanation (string).
Each suggestion: {type, description, code_before, code_after}
```

**Critical:** CP3 deadline cuối W4. FE team (Đạt) block ở đây.

---

#### AI2-07 — Redis Cache (W4)
**Mục tiêu:** Tránh gọi LLM 2 lần với cùng code → tiết kiệm chi phí + tăng tốc

**Key design:**
```python
cache_key = SHA256(code + language)  # deterministic
TTL = 86400  # 24 giờ
```

**Flow:**
```
Request → check Redis → HIT: return <100ms → MISS: run pipeline → save Redis
```

---

### ITER 3 (Tuần 5-6): Swap sang local model

#### AI2-08 — Swap Ollama (W5-6)
**Mục tiêu:** Thay OpenAI bằng model fine-tune của AI1 (Ân)

**Tại sao Ollama?**
- Serve local model qua REST API giống OpenAI format
- Không thay đổi pipeline — chỉ đổi base URL + model name
- Chạy được trên server thường, không cần GPU cao cấp khi inference

**Process:**
1. Nhận SafeTensors từ AI1 (link HuggingFace/Drive)
2. Convert sang GGUF format (nếu cần) bằng `llama.cpp`
3. Tạo `Modelfile` cho Ollama
4. `OllamaClient` thay `OpenAIClient` — interface giống nhau

**Design pattern quan trọng:** Interface abstraction
```python
class LLMClient(ABC):
    @abstractmethod
    async def complete(self, prompt: str) -> str: ...

class OpenAIClient(LLMClient): ...   # dùng Iter 2
class OllamaClient(LLMClient): ...  # dùng Iter 3+
```
→ Swap model = đổi 1 dòng config, không sửa pipeline

---

#### AI2-09 — Lưu lịch sử MongoDB (W5)
**Mục tiêu:** Premium users có lịch sử toàn bộ analysis

**Schema collection `ai_analysis_history`:**
```json
{
  "_id": "ObjectId",
  "user_id": "string",
  "input_code": "string",
  "language": "string",
  "output": { "suggestions": [], "race_conditions": [] },
  "tokens_used": 420,
  "model": "openai/ollama",
  "created_at": "ISODate",
  "cached": false
}
```

**API:** `GET /history/{user_id}?page=1&limit=20`

---

### ITER 4 (Tuần 7-8): Tối ưu & Deploy

#### AI2-10 — Queue & Load Test & Docker (W7-8)
**Mục tiêu:** Hệ thống ổn định với 10 concurrent users

**Queue design:**
```python
semaphore = asyncio.Semaphore(3)  # max 3 LLM calls đồng thời

async def analyze(request):
    async with semaphore:  # queue tự động
        result = await run_pipeline(request)
    return result
```

**Error responses:**
- Semaphore đầy → `429 Too Many Requests` + `retry_after: 10`
- Timeout 30s → `504 Gateway Timeout`

**Docker Compose:**
```yaml
services:
  fastapi:    # AI server
  redis:      # cache
  ollama:     # local LLM
```

**Load test target:** 10 concurrent users, p95 < 15s, no crash

---

## 5. Phụ thuộc với AI1 (Ân)

| Mình cần từ AI1 | Khi nào | Task của mình |
|-----------------|---------|---------------|
| `ast_preprocessor.py` — module phân tích AST | Cuối W2 | AI2-03 (race detector) |
| Model SafeTensors + link | Cuối W5 | AI2-08 (swap Ollama) |
| `output_parser.py` — parse output model | Cuối W6 | AI2-08 (tích hợp) |

**Backup plan:** Nếu AI1 trễ:
- Race detector: tự viết AST parser đơn giản bằng `acorn` (JS) hoặc `ast` module (Python)
- Model: giữ OpenAI thêm 1 tuần
- Output parser: tự viết regex parser tạm

---

## 6. Tech Stack cụ thể

| Thành phần | Technology | Lý do |
|-----------|-----------|-------|
| API Server | FastAPI + uvicorn | Async, Python-native AI libs |
| BM25 Search | `rank-bm25` | Nhẹ, không cần GPU |
| LLM (tạm) | OpenAI GPT-3.5-turbo | Fast, reliable cho dev |
| LLM (final) | Ollama + model AI1 | Self-hosted, free inference |
| Cache | Redis + `redis-py` | TTL, fast lookup |
| Database | MongoDB + `motor` | Async driver, flexible schema |
| Auth | JWT verify (shared secret với Node.js) | |
| Containerize | Docker Compose | |
| Load test | `locust` hoặc `k6` | |

---

## 7. Checkpoint quan trọng nhất

**CP3 — Cuối tuần 4** là checkpoint sống còn:
- FastAPI `/analyze` phải hoạt động với OpenAI
- FE team (Đạt) cần để build giao diện phân tích AI
- Trễ → dùng mock response để unblock FE

**CP6 — Cuối tuần 6** là milestone kỹ thuật:
- Full pipeline: Code → AST → BM25 → Ollama → Response
- Demo nội bộ cả nhóm

---

## 8. Thứ tự bắt đầu (ngay bây giờ)

```
W1: AI2-01 (Knowledge Base) → song song AI2-02 (BM25 setup)
W2: AI2-03 (Race Detector) → AI2-04 (Report Formatter)
W3: AI2-05 (FastAPI) → bắt đầu AI2-06 (RAG)
W4: Hoàn thiện AI2-06 → AI2-07 (Redis) → ✅ CP3
...
```

Task đầu tiên cần làm ngay: **AI2-01 — thu thập và format 250+ docs knowledge base**
