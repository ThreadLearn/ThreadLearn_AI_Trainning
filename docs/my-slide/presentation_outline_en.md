# 🎯 THREADLEARN PRESENTATION SCRIPT (English)

---

## PART 1 — THE PAIN (Problem & Motivation) ⏱ ~2 min

### 1.1. JavaScript Concurrency Bugs — Everyone Hits Them, Few Notice

> **Speaker:** Show the audience this is a REAL problem, not an academic exercise.

| Key Point | Evidence |
|-----------|----------|
| JS runs single-threaded event loop, but async code causes real concurrency bugs | 93% of real-world bugs cause crash/data corruption/server hang (NodeCB, ASE 2017) |
| Concrete example: **Checkout race condition** — 2 users buy last product simultaneously, both see "1 left", both succeed → negative inventory | Show before/after code slide |
| Developers don't notice because solo tests always PASS; only fail under real concurrent load | Slide: "code alone: OK / 1000 users: DEAD" |

### 1.2. Existing Tools Fall Short

| Tool | Detects? | Auto-fixes? | Offline? |
|------|:---:|:---:|:---:|
| ESLint | ✅ Yes | ❌ No | ✅ |
| GPT-3.5/4 | ⚠️ 30% | ✅ Yes | ❌ Needs API + $ |
| **ThreadLearn** | ✅ | ✅ | ✅ Free |

> **Bridge to Trung:** "To build an AI system that does all three — detect, fix, and run offline — we split the work into two parts..."

---

## PART 2 — TRUNG (AI2) ⏱ ~5 min

> **Trung:** "I own the entire **serving** system — receiving code from users, analyzing it, returning results. Three main blocks."

### 2.1. Knowledge Base + BM25 Search Engine

```
2050 JavaScript concurrency documents
           │
           ▼
    BM25 Index (loads in RAM, <500ms)
           │
           ▼
  Retrieve top-3 most relevant docs → inject into LLM prompt
```

| Technical Highlight | Detail |
|--------------------|--------|
| **Why BM25 instead of Vector Search?** | No GPU needed, no embedding model, keyword search matches API names exactly (`setTimeout`, `Promise.all`) |
| **CamelCase-aware Tokenizer** | `fetchAllUsers` → `["fetch", "all", "users"]`; `appendFile` stays intact, not split into `append file` |
| **Auto-stopwords** | IDF-based automatic stopword filtering when scaling to 5000+ docs |

### 2.2. Race Condition Detector (Static Analysis)

```
10 patterns × (JS + Python)
├── JS:  closure_loop_var, shared_var_settimeout, promise_no_await, concurrent_write_array, counter_no_atomic
└── Python: global_var_thread, shared_list_no_lock, thread_read_write_race, missing_join, singleton_lazy_init
```

| Highlight | |
|----------|-----|
| Rule-based on AST nodes — **fast, no LLM needed** | |
| Integrates `ast_preprocessor.py` from AI1 (Ân) — shared module | |
| Dedup + false-positive suppression (Lock present → don't flag) | |

### 2.3. FastAPI Server + RAG Pipeline

```
┌─────────────────────────────────────────────────────┐
│  POST /api/v1/ai/analyze  {code, language}          │
│         │                                           │
│         ├─► JWT Verify (Node.js backend)            │
│         ├─► Redis Cache? ── HIT ──► return instantly│
│         ├─► AST Extract Keywords (esprima)          │
│         ├─► BM25 Search top-3 docs                  │
│         ├─► Build Prompt = docs + code              │
│         ├─► LLM Inference (Semaphore max 3)         │
│         ├─► Race Detector scan                      │
│         ├─► Format JSON Response                    │
│         ├─► Save MongoDB (history)                  │
│         └─► Set Redis (TTL 24h)                     │
└─────────────────────────────────────────────────────┘
```

| Infrastructure | |
|---------------|-----|
| **Redis Cache** | SHA256(code+language), TTL 24h, graceful degradation |
| **MongoDB History** | Motor async, paginated `/history/{user_id}?page=1&limit=20` |
| **Concurrency Control** | `asyncio.Semaphore(3)` — prevents GPU OOM |
| **Docker Compose** | FastAPI + Redis + MongoDB + Ollama |

| Load Test Results | |
|-------------------|---|
| Throughput | **86 req/s** |
| P50 latency | **3.2 ms** |
| P95 latency | **112 ms** |

### 2.4. Challenges & How We Overcame Them (Trung)

| Challenge | Solution |
|-----------|----------|
| FE team (Đạt) blocked — no API yet | Ship Mock LLM early (CP3) → FE unblocked, swap real LLM later |
| GPU OOM under concurrent requests | Semaphore(3) + auto queue |
| Redis/MongoDB unavailable | Graceful degradation — server never crashes |
| Prompt format mismatch between training & inference | Collaborated with Ân to debug → rewrote eval script with correct format |

> **Bridge to Ân:** "The serving system is ready, but we need a model powerful enough to truly UNDERSTAND and FIX concurrency bugs — that's Ân's part."

---

## PART 3 — ÂN (AI1) ⏱ ~5 min

> **Ân:** "I own the **heart** of the system — the AI model. Mission: teach a 1.5B parameter model to understand and fix JavaScript concurrency bugs."

### 3.1. Dataset — Garbage In, Garbage Out

```
Data Sources:
├── GitHub Code Search (15 query patterns) → real commits
├── Synthetic Pairs (60 hand-written pairs, 8 categories)
└── Data Augmentation (100 samples for weak patterns)

Result: 783 pairs (buggy code → fixed code)
        Train 90% (704) / Eval 10% (79)
        Shuffle seed=42 (reproducible)
```

| Highlight | |
|-----------|-----|
| **Why completion format, not chat format?** | Task is "see code → generate fix", not a conversation. Wrong format → pass rate drops from 70% to 35% |
| **AST data cleaning** | `@babel/parser` normalizes code, strips junk comments, preserves API names |
| **Data Augmentation** | 100 synthetic samples for 4 critical patterns + 9 targeted samples for 5 weak patterns |

### 3.2. QLoRA Fine-tuning — 8× VRAM Savings

```
Base model Qwen2.5-Coder-1.5B (3GB float16)
    ↓ Load 4-bit quantization (NF4) → ~800MB VRAM
    ↓ Add LoRA adapter (r=16) → trains only 0.5% of parameters
    ↓ Train on Kaggle (2× T4 GPU, free)
    ↓ ~500 steps, ~2 hours
    ↓ Merge adapter into base → Complete 3GB model
```

| Config | Value | Why |
|--------|-------|-----|
| `r=16, alpha=32` | Balances efficiency / memory |
| `4-bit NF4 + Double Quant` | VRAM: 12GB → 4GB |
| `gradient_accumulation=8` | "Fakes" batch size 8 with 1 sample/step |
| `lr=2e-4, cosine decay` | Fast early learning, smooth at end |
| `max_steps=500` | Prevents overfitting on small dataset |

### 3.3. Lessons Learned — Hard-Earned Experience

| # | Error | Consequence | Fix |
|---|-------|-------------|-----|
| 1 | Windows filename `model (1).safetensors` | Model won't load | Use `huggingface-cli download` |
| 2 | Unicode `→` crashes on Windows cp1252 | Eval script fails | Use ASCII `->` or `chcp 65001` |
| 3 | SFTTrainer API changed (`text_field`) | Training fails | Map dataset to create `"text"` column |
| **4** | **Prompt Format Mismatch** | **Pass rate 35% instead of 70%** | **Use identical format for train/eval** |
| 5 | 18/20 (90%) from mock, not real inference | Wrong report numbers | Always run real inference before writing reports |
| 6 | `get_peft_model()` commented out | Thought it was a bug — newer SFTTrainer auto-applies | Read changelog when upgrading libraries |
| 7 | Merge model requires CPU fp16 | Can't merge on 4-bit GPU | `device_map="cpu"` + `torch.float16` |

### 3.4. Results — Numbers Speak

| Method | Pass Rate |
|--------|-----------|
| GPT-3.5-turbo zero-shot | **30%** |
| Qwen2.5-Coder-1.5B (no fine-tune) | 40% |
| **ThreadLearn RAW** (fine-tuned, no RAG) | **70%** |
| **ThreadLearn + RAG** (fine-tuned + BM25) | **75%** 🏆 |

| Real-world 30-case (production npm bugs) | |
|------------------------------------------|-----|
| Base model (no fine-tune) | 60% |
| Merged v1 + pipeline | **73.3%** 🏆 |
| GPT-3.5-turbo + pipeline | 65% |

> **Takeaway:** A 1.5B model fine-tuned on domain-specific data **beats GPT-3.5** (175B) despite being **~125× smaller**. Domain-specific fine-tuning > general-purpose LLM.

---

## PART 4 — CONCLUSION ⏱ ~1 min

> **Both present, alternating:**

| Speaker | Key Message |
|---------|-------------|
| **Trung** | "Complete serving system: RAG pipeline + cache + history + load test. Runs offline, free, P95 = 112ms." |
| **Ân** | "1.5B model beats GPT-3.5. Secret: clean dataset + efficient QLoRA + correct prompt format." |
| **Both** | "ThreadLearn = Fine-tuned LLM + RAG Pipeline → Detects & fixes JS concurrency bugs, runs entirely offline on an 8GB VRAM laptop." |

### Real-World Applications (final slide)

```
📌 IDE Extension (VS Code) → highlight bugs on file save
📌 CI/CD Gate (GitHub Actions) → block PRs with race conditions
📌 Educational Tool (FPT University) → automated code review
📌 Code Review Assistant → comment fix suggestions on PRs
```

---

## 📋 APPENDIX: Suggested Slide Deck

| Slide | Speaker | Content |
|-------|---------|---------|
| 1 | Both | Title + Team |
| 2 | Both | The Pain: JS concurrency bugs + race condition example |
| 3 | Both | Existing tools fall short → What ThreadLearn solves |
| 4 | Both | Overall Architecture (diagram) |
| 5 | Trung | Knowledge Base + BM25 |
| 6 | Trung | Race Condition Detector (10 patterns) |
| 7 | Trung | FastAPI Server + RAG Pipeline flow |
| 8 | Trung | Infrastructure: Redis, MongoDB, Docker, Load Test |
| 9 | Ân | Dataset: sources, format, numbers |
| 10 | Ân | QLoRA Fine-tuning: config, rationale |
| 11 | Ân | Lessons Learned — 7 errors + fixes |
| 12 | Ân | Results: Pass Rate table + Real-world benchmark |
| 13 | Both | Real-world applications + Conclusion |
 
