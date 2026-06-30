# AI2 Progress Tracker — Trung (AI Engineer 2)

**Last updated:** 2026-06-08
**Engineer:** Trung (letritrung2605@gmail.com)
**Role:** AI Engineer 2 — Knowledge Base, BM25 Retrieval, Race Condition Detection, FastAPI Server, RAG Pipeline

---

## Status Legend

| Symbol | Meaning |
|---|---|
| ✅ DONE | Task complete, output delivered |
| 🔄 IN PROGRESS | Currently being worked on |
| ⏳ PENDING | Not started, dependencies met or approaching |
| 🚫 BLOCKED | Cannot start — waiting on another task |

---

## Progress Summary Table

| Task ID | Task Name | Iter | Week(s) | Priority | Est. Days | Status | Notes |
|---|---|---|---|---|---|---|---|
| AI2-01 | Xây dựng Knowledge Base | 1 | W1 | High | 4d | ✅ DONE | 250 docs delivered |
| AI2-02 | BM25 Indexing Module | 1 | W1-2 | High | 4d | ✅ DONE | 18 tests pass, auto_stopwords.py sẵn sàng |
| AI2-03 | Race Condition Detection | 1 | W2 | High | 5d | ✅ DONE | 10 patterns, 20 tests pass, tích hợp ast_preprocessor |
| AI2-04 | Race Condition Report | 1 | W2 | Medium | 2d | ✅ DONE | format_report(), 22 tests pass |
| AI2-05 | FastAPI Server Setup | 2 | W3 | High | 4d | ✅ DONE | 3 routes, JWT auth, 7 tests pass |
| AI2-06 | RAG Pipeline (OpenAI temp) | 2 | W3-4 | High | 6d | ✅ DONE | Mock LLM tạm, pipeline E2E hoạt động |
| AI2-07 | Redis Caching Layer | 2 | W4 | Medium | 3d | ✅ DONE | SHA256 key, TTL 24h, 11 tests pass |
| AI2-08 | Swap Local Model (Ollama) | 3 | W5-6 | High | 4d | 🚫 BLOCKED | Blocked on AI1-07 SafeTensors (Ân) |
| AI2-09 | Lưu lịch sử MongoDB | 3 | W5 | Medium | 3d | ✅ DONE | Motor async, paginated /history, 9 tests pass |
| AI2-10 | Queue & Load Test | 4 | W7-8 | High | 5d | 🔄 PARTIAL | Semaphore+Docker done; load test pending AI2-08 |

**Completed: 9 / 10 tasks** (+ AI2-10 partial)

---

## Dependencies Diagram (ASCII)

```
AI2-01 (Knowledge Base)
  └─► AI2-02 (BM25 Indexing) ✅
        └─► AI2-06 (RAG Pipeline) ✅ ◄─── AI2-05 (FastAPI Server) ✅ ◄─── AI2-07 (Redis Cache) ✅
                │                                                                    │
                │                                                               AI2-09 (MongoDB History) ⏳
                ▼
          AI2-08 (Ollama Swap) 🚫 [blocked on AI1-07]
                └─► AI2-10 (Queue & Load Test) ⏳ ◄─── AI2-07 ✅

AI1-03 (AST Preprocessor) ──► AI2-03 (Race Condition Detection) 🚫
                                     └─► AI2-04 (Race Condition Report) 🚫
                          └──────────► AI2-06 (RAG Pipeline) ✅ [dùng mock fallback]

AI1-07 (SafeTensors Model) ──► AI2-08 (Ollama Swap) 🚫
```

---

## Checkpoints

| CP | Name | Deliverable | Target Week | Status |
|---|---|---|---|---|
| CP1 | Knowledge Base ready | knowledge_base.json (250 docs) | W1 | ✅ DONE |
| CP2 | BM25 retrieval unit tests pass | bm25_module.py, 18 tests pass | W2 | ✅ DONE |
| CP3 | /analyze endpoint returns results | FastAPI + RAG pipeline E2E, mock LLM | W4 | ✅ DONE |
| CP4 | Race condition detection integrated | race_detector.py + report_formatter.py | W2-3 | ✅ DONE |
| CP5 | Redis cache working | 2nd identical request cached, 11 tests pass | W4 | ✅ DONE |
| CP6 | Ollama model swapped in | Local model pipeline, comparison report | W6 | 🚫 BLOCKED |
| CP7 | History API working | MongoDB collection, paginated GET /history | W5 | ✅ DONE |
| CP8 | Load test pass + Docker Compose | k6/locust results, docker-compose.yml | W8 | ⏳ PENDING |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| AI1-03 (AST preprocessor) delayed | Medium | High | Mock fallback đã active trong rag_pipeline.py — tokenize() trên raw code |
| AI1-07 (SafeTensors model) delayed | Medium | High | OpenAI mock tạm trong llm_client.py; OllamaClient có thể code trước |
| FE team (Đạt) blocked on CP3 | ✅ Resolved | — | /analyze endpoint đã live với mock LLM |
| GPU OOM under concurrent load | Medium | High | Semaphore(3) trong AI2-10 |
| Redis unavailable in dev | Low | Medium | Graceful degradation đã implement — server không crash |
| OpenAI API costs exceed budget | Low | Medium | Cache (AI2-07) giảm duplicate calls; Ollama sẽ thay thế hoàn toàn |
| knowledge_base.json quality | Low | Medium | 250 docs reviewed, 18 BM25 tests bao phủ retrieval |

---

## Commit History

| Commit | Date | Task | Summary |
|---|---|---|---|
| (early) | 2026-05 | AI2-01 | knowledge_base.json — 250 docs (171 patterns, 35 anti-patterns, 44 race-conditions) |
| (early) | 2026-05 | AI2-02 | bm25_module.py — BM25Retriever, tokenize CamelCase-aware, load_retriever |
| 1f09753 | 2026-05 | AI2-02 | Vietnamese comments + auto_stopwords.py + formula doc |
| cf3a4fb | 2026-05-26 | AI2-05/06 | FastAPI server — 3 routes, JWT auth, rag_pipeline, llm_client mock, schemas |
| 1b67755 | 2026-05-31 | AI2-07 | Redis cache layer — cache.py, test_cache.py (11 tests), conftest.py |
| f4a1e49 | 2026-05-31 | AI2-09 | MongoDB history — db.py, save_analysis(), paginated GET /history, 9 tests |
| 39a8d1c | 2026-05-31 | AI2-04/10 | Report formatter (format_report, 22 tests) + Queue/Docker prep (Semaphore, Dockerfile, locustfile) |
| 720ac5d | 2026-06-01 | skill | run-ai2-server skill — smoke.sh + SKILL.md, E2E verified all 3 endpoints |
| da781f0 | 2026-06-08 | AI2-03 | race_detector.py — 10 patterns (5 JS, 5 Py), 20 tests pass, ast_preprocessor integrated |

Branch: `AI-2-Trung` → `develop` → `master`

---

## Task Details

---

### AI2-01 — Xây dựng Knowledge Base

| Field | Value |
|---|---|
| Task ID | AI2-01 |
| Full Name | Xây dựng Knowledge Base (Build Knowledge Base) |
| Iteration | 1 |
| Week(s) | W1 |
| Dependencies | None |
| Output / Deliverable | `ai2-knowledge-base/knowledge_base.json` — 250 documents |
| Priority | High |
| Estimated Days | 4d |
| Status | ✅ DONE |

**Subtask Checklist:**

- [x] Thu thập tài liệu về concurrent patterns trong JavaScript
- [x] Format mỗi doc theo schema `{id, title, content, language, category, source, url}`
- [x] Phân loại: `patterns`, `anti-patterns`, `race-conditions`
- [x] Lưu vào JSON array
- [x] Loại bỏ tài liệu trùng lặp
- [x] Đạt ~250 docs

**Actual Results:**

| Category | Count |
|---|---|
| patterns | 171 |
| anti-patterns | 35 |
| race-conditions | 44 |
| **Total** | **250** |

---

### AI2-02 — BM25 Indexing Module

| Field | Value |
|---|---|
| Task ID | AI2-02 |
| Full Name | BM25 Indexing Module |
| Iteration | 1 |
| Week(s) | W1-2 |
| Dependencies | AI2-01 (met) |
| Output / Deliverable | `bm25_module.py` + `auto_stopwords.py` — 18 unit tests pass |
| Priority | High |
| Estimated Days | 4d |
| Status | ✅ DONE |

**Subtask Checklist:**

- [x] `pip install rank-bm25`
- [x] `BM25Retriever.build(docs)` — tokenize + build BM25Okapi index, hold in RAM
- [x] Tokenization: lowercase + STOPWORDS + CamelCase splitting (fetchAllUsers → fetch, All, Users)
- [x] Verify index load time <500ms for 250 docs
- [x] `BM25Retriever.search(query, top_k=3)` — trả top 3 docs theo BM25 score
- [x] 18 unit tests pass (test_bm25.py)
- [x] auto_stopwords.py — IDF-based auto stopwords cho khi scale ≥5000 docs
- [x] load_retriever() tự chọn strategy: <5000 → hard-code STOPWORDS, ≥5000 → IDF auto

**Key decisions:**
- "all" bị bỏ khỏi STOPWORDS — có nghĩa trong JS (Promise.all, fetchAllUsers)
- Hard-coded STOPWORDS cho 250 docs; auto_stopwords.py sẵn sàng khi scale

**Files:**
- `server/server/bm25_module.py`
- `server/server/auto_stopwords.py`
- `server/docs/auto_stopwords_formula.md`
- `server/tests/test_bm25.py`

---

### AI2-03 — Race Condition Detection

| Field | Value |
|---|---|
| Task ID | AI2-03 |
| Full Name | Race Condition Detection |
| Iteration | 1 |
| Week(s) | W2 |
| Dependencies | AI1-03 (ast_preprocessor.py) — ĐÃ NHẬN (Ân, 2026-06-05) |
| Output / Deliverable | `race_detector.py` — 10 patterns, 20/20 tests pass |
| Priority | High |
| Estimated Days | 5d |
| Status | ✅ DONE — 2026-06-08 |

**Subtask Checklist:**

- [x] Tích hợp `ast_preprocessor.py` từ AI1 — `stripComments`, `extractFunctions`, `extract_keywords`
- [x] JS Pattern 1: `closure_loop_var` — var + async callback trong for-loop
- [x] JS Pattern 2: `shared_var_settimeout` — var bị capture bởi setTimeout
- [x] JS Pattern 3: `promise_no_await` — async call không có await/.then
- [x] JS Pattern 4: `concurrent_write_array` — push vào array từ nhiều callback
- [x] JS/Py Pattern 5: `counter_no_atomic` — increment không atomic trong async context
- [x] Py Pattern 6: `global_var_thread` — global var trong thread không có Lock
- [x] Py Pattern 7: `shared_list_no_lock` — list.append từ nhiều thread không Lock
- [x] Py Pattern 8: `thread_read_write_race` — read-write race trong thread
- [x] Py Pattern 9: `missing_join` — thread không có .join()
- [x] Py Pattern 10: `singleton_lazy_init` — lazy init không Lock (TOCTOU)
- [x] Dedup: bỏ detection trùng pattern_id + line_range
- [x] Graceful fallback nếu ast_preprocessor không import được
- [x] 20 unit tests pass (11 positive, 5 false-positive, 4 structure/integration)

**Key decisions:**
- Import ast_preprocessor qua `sys.path` relative — không hardcode absolute path
- FP suppression: có Lock bất kỳ đâu trong file → không flag shared_list/thread_read_write/singleton
- JS: TypeScript treated as JavaScript (tái dùng cùng detectors)
- `detectRaceConditions()` → `format_report()` pipeline hoạt động end-to-end

**Files:**
- `server/server/race_detector.py`
- `server/tests/test_race_detector.py`

---

### AI2-04 — Race Condition Report

| Field | Value |
|---|---|
| Task ID | AI2-04 |
| Full Name | Race Condition Report (Formatter) |
| Iteration | 1 |
| Week(s) | W2 |
| Dependencies | AI2-03 |
| Output / Deliverable | `report_formatter.py` — JSON output schema valid |
| Priority | Medium |
| Estimated Days | 2d |
| Status | 🚫 BLOCKED (waiting on AI2-03) |

---

### AI2-05 — FastAPI Server Setup

| Field | Value |
|---|---|
| Task ID | AI2-05 |
| Full Name | FastAPI Server Setup |
| Iteration | 2 |
| Week(s) | W3 |
| Dependencies | None |
| Output / Deliverable | FastAPI app — 3 routes hoạt động, 7 integration tests pass |
| Priority | High |
| Estimated Days | 4d |
| Status | ✅ DONE — commit cf3a4fb (2026-05-26) |

**Subtask Checklist:**

- [x] `pip install fastapi uvicorn pydantic python-jose`
- [x] Initialize FastAPI app với lifespan (startup: build BM25 index)
- [x] `POST /api/v1/ai/analyze` — main analysis endpoint (JWT auth)
- [x] `GET /api/v1/ai/history/{user_id}` — mock empty list (TODO AI2-09)
- [x] `GET /health` — health check, public
- [x] JWT verify (python-jose HS256, khớp với Node.js backend)
- [x] Pydantic request/response models (schemas.py)
- [x] 7 integration tests pass (test_main.py)

**Key decisions:**
- Mock LLM tạm để FE (Đạt) unblock ngay
- History route check `current_user == user_id` → 403 nếu xem của người khác
- lifespan context manager cho BM25 startup load

**Files:**
- `server/server/main.py`
- `server/server/schemas.py`
- `server/server/auth.py`
- `server/server/llm_client.py`
- `server/server/rag_pipeline.py`
- `server/tests/test_main.py`

---

### AI2-06 — RAG Pipeline (OpenAI tạm)

| Field | Value |
|---|---|
| Task ID | AI2-06 |
| Full Name | RAG Pipeline (OpenAI temporary) |
| Iteration | 2 |
| Week(s) | W3-4 |
| Dependencies | AI2-02 ✅, AI2-05 ✅, AI1-03 (mock fallback dùng tạm) |
| Output / Deliverable | `POST /api/v1/ai/analyze` trả issues + docs_used — pipeline E2E hoạt động |
| Priority | High |
| Estimated Days | 6d |
| Status | ✅ DONE (mock LLM — thay thật khi AI2-08 unblock) |

**Pipeline flow (hiện tại):**
```
code → tokenize() first 20 tokens → BM25 search top-3 docs
     → build_prompt() → mock LLM → List[Issue]
     → AnalyzeResponse {user_id, language, issues, docs_used, cached}
```

**Key decisions:**
- `LLM_PROVIDER=mock` mặc định — không cần OpenAI key để chạy
- `LLM_PROVIDER=openai` → NotImplementedError (AI2-08 sẽ implement)
- llm_client.py dùng strategy pattern → swap LLM không đổi pipeline

**Files:**
- `server/server/rag_pipeline.py`
- `server/server/llm_client.py`

---

### AI2-07 — Redis Caching Layer

| Field | Value |
|---|---|
| Task ID | AI2-07 |
| Full Name | Redis Caching Layer |
| Iteration | 2 |
| Week(s) | W4 |
| Dependencies | AI2-05 ✅ |
| Output / Deliverable | Cache working — SHA256 key, TTL 24h, 11 tests pass |
| Priority | Medium |
| Estimated Days | 3d |
| Status | ✅ DONE — commit 1b67755 (2026-05-31) |

**Subtask Checklist:**

- [x] `pip install redis` (redis.asyncio)
- [x] `make_cache_key(code, language)` — SHA256 → `ai2:analysis:<64hex>`
- [x] `get_cached()` — Redis GET, trả AnalyzeResponse hoặc None
- [x] `set_cached()` — Redis SETEX với TTL 86400s
- [x] `invalidate()` — xóa key thủ công
- [x] Tích hợp vào `/analyze` route (check trước pipeline, set sau)
- [x] Graceful degradation — Redis down không crash server
- [x] 11 integration tests pass (test_cache.py)
- [x] conftest.py — centralized sys.path setup

**Key decisions:**
- Key format: `ai2:analysis:<SHA256(code|language)>` — namespace safe, 64 hex cố định
- TTL 86400s (24h)
- `socket_connect_timeout=1s` — fail fast khi Redis không có
- Mọi exception → None/False, không bao giờ raise lên route
- test_main.py phải patch `llm_client.LLM_PROVIDER` trực tiếp (không qua os.environ) vì config.py đã bind tại import time

**Files:**
- `server/server/cache.py`
- `server/tests/test_cache.py`
- `server/tests/conftest.py`

---

### AI2-08 — Swap Local Model (Ollama)

| Field | Value |
|---|---|
| Task ID | AI2-08 |
| Full Name | Swap Local Model (Ollama) |
| Iteration | 3 |
| Week(s) | W5-6 |
| Dependencies | AI1-07 (SafeTensors model từ Ân), AI2-06 ✅ |
| Output / Deliverable | Ollama pipeline running — latency + quality comparison report |
| Priority | High |
| Estimated Days | 4d |
| Status | 🚫 BLOCKED (waiting on AI1-07 từ Ân) |

**Có thể chuẩn bị trước:** `OllamaClient` code trong llm_client.py + `Modelfile` template — không cần model weights.

---

### AI2-09 — Lưu lịch sử MongoDB

| Field | Value |
|---|---|
| Task ID | AI2-09 |
| Full Name | Lưu lịch sử phân tích MongoDB |
| Iteration | 3 |
| Week(s) | W5 |
| Dependencies | AI2-05 ✅ |
| Output / Deliverable | MongoDB collection `ai_analysis_history` — GET /history trả data thật, có phân trang |
| Priority | Medium |
| Estimated Days | 3d |
| Status | ⏳ PENDING — sẵn sàng làm (NEXT TASK) |

**Subtask Checklist:**

- [ ] `pip install motor` (async MongoDB driver)
- [ ] `server/server/db.py` — MongoDB connection, collection ref
- [ ] Document schema: `{_id, user_id, input_code, language, issues, docs_used, model, cached, created_at}`
- [ ] `save_analysis(user_id, ...) -> ObjectId`
- [ ] Index: `(user_id, 1), (created_at, -1)` cho pagination hiệu quả
- [ ] Cập nhật `/analyze` route — lưu kết quả vào MongoDB sau mỗi phân tích
- [ ] `GET /api/v1/ai/history/{user_id}` — query MongoDB thật, hỗ trợ `?page=1&limit=20`
- [ ] Cập nhật HistoryResponse schema — thêm `total`, `page`, `limit`
- [ ] 5 integration tests: insert → query → pagination đúng thứ tự

**MongoDB document schema:**

```json
{
  "_id": "ObjectId",
  "user_id": "string",
  "input_code": "string",
  "language": "string",
  "issues": [],
  "docs_used": [],
  "model": "mock|openai|ollama",
  "cached": false,
  "created_at": "ISODate"
}
```

---

### AI2-10 — Queue & Load Test

| Field | Value |
|---|---|
| Task ID | AI2-10 |
| Full Name | Queue & Load Test |
| Iteration | 4 |
| Week(s) | W7-8 |
| Dependencies | AI2-08 🚫, AI2-07 ✅ |
| Output / Deliverable | Load test results (10 concurrent users, p95 <15s, 0 crashes) + `docker-compose.yml` |
| Priority | High |
| Estimated Days | 5d |
| Status | ⏳ PENDING |

**Có thể chuẩn bị trước:** docker-compose.yml + locust/k6 scripts trong W6 khi AI2-08 còn blocked.
