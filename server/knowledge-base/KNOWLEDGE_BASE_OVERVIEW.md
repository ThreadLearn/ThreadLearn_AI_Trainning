# Knowledge Base Overview

## What It Is and Why It Exists

`knowledge_base.json` is the static document corpus that powers the BM25 retrieval step in the ThreadLearn AI2 analysis pipeline. It is a RAG (Retrieval-Augmented Generation) source: instead of relying solely on a general-purpose LLM to reason about concurrency patterns and race conditions, the pipeline retrieves the top 3 most relevant reference documents from this knowledge base and injects them directly into the LLM prompt as grounding context. This improves answer accuracy for JavaScript concurrency topics without requiring fine-tuning.

The file is loaded once at FastAPI server startup. The BM25 index is built in RAM from all 2,050 documents and remains there for the lifetime of the server process.

---

## Stats (verified against `knowledge_base.json`, current)

| Metric | Value |
|---|---|
| Total documents | 2,050 |
| Category: patterns | 1,418 |
| Category: anti-patterns | 280 |
| Category: race-conditions | 352 |
| Language | JavaScript only |

**By source:**

| Source | Count |
|---|---|
| Synthetic Data (Context Permutation) | 1,750 |
| ThreadLearn Knowledge Base (handwritten) | 151 |
| MDN Web Docs | 99 |
| RxJS Official Docs | 20 |
| p-limit GitHub | 10 |
| async-mutex Docs | 10 |
| Bluebird Docs | 10 |

The corpus grew from an initial 250-document seed (99 MDN + 151 handwritten) to 2,050 documents primarily through **synthetic permutation** — a template engine expands each handwritten/MDN document over multiple domain contexts and phrasings (same underlying concurrency concept, varied surface text), producing 1,750 additional documents. This scaling exists to give BM25 more surface-form variety to match against real-world query phrasing, not to introduce new concurrency concepts beyond the original 250.

---

## File Location

```
server/knowledge-base/knowledge_base.json
```

---

## Document Schema

Every document in the JSON array conforms to this schema:

```json
{
  "id":       "js-001",
  "title":    "Promise.all — Concurrent Promise Execution",
  "content":  "...",
  "language": "javascript",
  "category": "patterns",
  "source":   "MDN Web Docs",
  "url":      "https://developer.mozilla.org/..."
}
```

| Field | Type | Notes |
|---|---|---|
| `id` | string | `js-NNN` (js-001 to js-250) for the original seed corpus; `js-synth-<hash>` for synthetically generated documents. |
| `title` | string | Human-readable name for the pattern or topic. |
| `content` | string | Full explanatory text used for BM25 tokenization and LLM context injection. |
| `language` | string | Always `"javascript"` in the current corpus. |
| `category` | string | One of: `"patterns"`, `"anti-patterns"`, `"race-conditions"`. |
| `source` | string | One of the source labels in the table above. |
| `url` | string | Reference URL (MDN/official docs page, or empty string for handwritten/synthetic docs). |

---

## Category Descriptions

### patterns (1,418 documents)

Correct, idiomatic approaches to JavaScript concurrency and asynchronous programming. Seed topics (before synthetic expansion) include:

- `Promise.all` and `Promise.race` — parallel execution, short-circuit semantics
- `Promise.allSettled`, `Promise.any` — handling mixed success/failure
- `async/await` — structured asynchronous control flow
- Web Workers — off-main-thread computation, `postMessage` communication
- `SharedArrayBuffer` and `Atomics` — shared memory between workers, atomic read-modify-write
- Streams API — `ReadableStream`, `WritableStream`, `TransformStream`, `pipeThrough`, `pipeTo`
- Generators and `AsyncGenerators` — lazy iteration, pull-based data production
- `EventSource`, WebSocket, WebTransport — real-time and duplex communication
- `AbortController` / `AbortSignal` — cooperative cancellation of fetch and other async ops
- `AsyncLocalStorage` (Node.js) — async context propagation (request-scoped storage)
- Node.js `cluster` module and stream piping
- Async Semaphore / Mutex — concurrency limiting, mutual exclusion for async critical sections
- Async task graphs, event sourcing with async projections, polling with exponential backoff

### anti-patterns (280 documents)

Common mistakes in JavaScript async code that lead to bugs, hangs, or degraded performance. Seed topics include:

- Callback hell — deeply nested callbacks, pyramid of doom
- Blocking the event loop in async code — synchronous CPU work inside async functions
- Fire-and-forget promises — launching async ops without storing or awaiting the promise
- Returning a non-awaited promise — losing error propagation
- Mixing sync and async paths non-uniformly — Zalgo-style bugs
- Using `Array.forEach` with async callbacks — no await, uncaught rejections
- Ignoring rejected promises — no `.catch()` and no `try/catch` around await
- Sequential `await` in a loop when parallel execution is possible

### race-conditions (352 documents)

Specific scenarios where concurrent execution produces incorrect results due to ordering or timing issues. Seed topics include:

- Shared variable modified inside `setTimeout` — two timers racing to read-modify-write the same variable
- Concurrent write to the same array — multiple async ops pushing to a shared array without coordination
- Closure capturing a mutable loop variable — classic `var i` in a for-loop with async callbacks
- Fetch deduplication race, concurrent session token validation, concurrent autocomplete cancellation
- TOCTOU (time-of-check/time-of-use) in async code — checking a condition then acting on it after an await that invalidates the check
- IndexedDB transaction races, WebSocket message ordering, Service Worker cache stampede

---

## How BM25 Uses This Knowledge Base

### Server Startup

```
FastAPI starts
  → load knowledge_base.json (2,050 docs)
  → buildIndex(docs)
      → for each doc: tokenize(content) → lowercase → remove stopwords → store term frequencies
      → compute IDF for all terms across corpus
      → BM25 index held in RAM (k1=1.5, b=0.75)
```

### Per-Request Flow (`POST /api/v1/ai/analyze`)

```
Incoming request {code, language, user_id}
  → AI2 AST preprocessor (esprima) extracts keywords from code
  → search(keywords, topK=3)
      → BM25 scores all 2,050 docs against query
      → returns top 3 docs by relevance score
  → 3 docs injected into LLM prompt as reference context
  → LLM generates suggestions grounded in retrieved docs
```

The BM25 retrieval ensures the LLM sees specific, relevant documentation for whatever concurrency pattern or anti-pattern is present in the submitted code, rather than relying on its general training data alone. See [`docs/RESEARCH_LOG.md`](../../docs/RESEARCH_LOG.md) for how this pipeline performs in the 30-case real-world benchmark (73.3% for the fine-tuned model + pipeline, vs. 63.3% without pipeline).

---

## How to Add More Documents

The file is a flat JSON array. To add new documents:

1. Open `server/knowledge-base/knowledge_base.json`.
2. Append new objects at the end of the array.
3. Use a unique `id` — `js-NNN` for handwritten seed docs (continue past `js-250`), or `js-synth-<hash>` if generated by the synthetic permutation script.
4. All 6 fields are required: `id`, `title`, `content`, `language`, `category`, `source`, `url`.
5. `language` must be `"javascript"` (or extend to other languages if the pipeline is updated).
6. `category` must be one of: `"patterns"`, `"anti-patterns"`, `"race-conditions"`.
7. Restart the FastAPI server so `buildIndex` runs again with the new docs.
8. If the corpus grows past 5,000 docs, `bm25_module.py`'s auto-stopwords threshold logic kicks in — see [`server/docs/auto_stopwords_formula.md`](../docs/auto_stopwords_formula.md).

---

## Status

**COMPLETE for the 30-case real-world benchmark reported in the paper.** The corpus has grown from the original 250-document seed (AI2-01) to 2,050 documents via `server/knowledge-base/augment_dataset.py` (synthetic context permutation). Further growth is possible by appending new handwritten or scraped documents per the process above.
