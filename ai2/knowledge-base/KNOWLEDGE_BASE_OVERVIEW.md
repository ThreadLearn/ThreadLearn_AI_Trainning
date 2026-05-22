# Knowledge Base Overview

## What It Is and Why It Exists

`knowledge_base.json` is the static document corpus that powers the BM25 retrieval step in the ThreadLearn AI2 analysis pipeline. It is a RAG (Retrieval-Augmented Generation) source: instead of relying solely on a general-purpose LLM to reason about concurrency patterns and race conditions, the pipeline retrieves the 3 most relevant reference documents from this knowledge base and injects them directly into the LLM prompt as grounding context. This improves answer accuracy for JavaScript concurrency topics without requiring fine-tuning.

The file is loaded once at FastAPI server startup. The BM25 index is built in RAM from all 250 documents and remains there for the lifetime of the server process.

---

## Stats

| Metric | Value |
|---|---|
| Total documents | 250 |
| Category: patterns | 171 |
| Category: anti-patterns | 35 |
| Category: race-conditions | 44 |
| Language | JavaScript only |
| Primary source | MDN Web Docs |
| Secondary source | Handwritten |

---

## File Location

```
ai2-knowledge-base/knowledge_base.json
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
| `id` | string | Sequential identifier. Format: `js-NNN`. Range: `js-001` to `js-250`. |
| `title` | string | Human-readable name for the pattern or topic. |
| `content` | string | Full explanatory text used for BM25 tokenization and LLM context injection. |
| `language` | string | Always `"javascript"` in the current corpus. |
| `category` | string | One of: `"patterns"`, `"anti-patterns"`, `"race-conditions"`. |
| `source` | string | `"MDN Web Docs"` or `"handwritten"`. |
| `url` | string | Reference URL (MDN page or empty string for handwritten docs). |

---

## Language

The entire corpus is JavaScript only. IDs run from `js-001` through `js-250`. All `language` fields are set to `"javascript"`.

---

## Source

- **MDN Web Docs** (primary): The majority of documents are derived from MDN reference pages covering Web APIs, concurrency primitives, and asynchronous JavaScript.
- **Handwritten**: A smaller subset of documents was authored manually to cover patterns and race conditions not directly documented on MDN (e.g., application-level race conditions, Node.js-specific patterns, and composite async idioms).

---

## Category Descriptions

### patterns (171 documents)

Correct, idiomatic approaches to JavaScript concurrency and asynchronous programming. Topics include:

- `Promise.all` and `Promise.race` — parallel execution, short-circuit semantics
- `Promise.allSettled`, `Promise.any` — handling mixed success/failure
- `async/await` — structured asynchronous control flow
- Web Workers — off-main-thread computation, `postMessage` communication
- `SharedArrayBuffer` and `Atomics` — shared memory between workers, atomic read-modify-write
- Streams API — `ReadableStream`, `WritableStream`, `TransformStream`, `pipeThrough`, `pipeTo`
- Generators and `AsyncGenerators` — lazy iteration, pull-based data production
- `EventSource` — server-sent events, reconnection handling
- WebSocket — full-duplex communication, event-driven messaging
- WebTransport — low-latency datagram and stream transport
- `OffscreenCanvas` — canvas rendering in a Worker
- Web Locks API — named locks for coordinating cross-tab resource access
- `IntersectionObserver`, `MutationObserver`, `ResizeObserver` — efficient DOM observation
- `BroadcastChannel` — cross-tab/worker publish-subscribe
- `MessageChannel` — two-way structured communication between contexts
- Scheduler API (`scheduler.postTask`) — priority-based task scheduling
- `AbortController` / `AbortSignal` — cooperative cancellation of fetch and other async ops
- `WeakRef` and `FinalizationRegistry` — memory-sensitive object tracking
- Service Workers — background fetch, cache strategies, push notifications
- Reactive Proxy patterns — observable state via `Proxy`/`Reflect`
- `AsyncLocalStorage` (Node.js) — async context propagation (request-scoped storage)
- Node.js `cluster` module — multi-process load distribution
- Node.js stream piping — composing readable/writable/transform streams
- Async Semaphore — concurrency limiting with a token pool
- Async Mutex — mutual exclusion for async critical sections
- Async task graphs — DAG-based dependency resolution for parallel subtasks
- Event sourcing with async projections — append-only event log + async read models
- Async polling with exponential backoff — retry loops with jitter and abort support
- Additional patterns covering structured concurrency, `queueMicrotask`, `requestIdleCallback`, `requestAnimationFrame` scheduling

### anti-patterns (35 documents)

Common mistakes in JavaScript async code that lead to bugs, hangs, or degraded performance. Topics include:

- Callback hell — deeply nested callbacks, pyramid of doom
- Blocking the event loop in async code — synchronous CPU work inside async functions
- Fire-and-forget promises — launching async ops without storing or awaiting the promise
- Returning a non-awaited promise — `async` function returns `promise` instead of `await promise`, losing error propagation
- Swallowing `AbortError` — catching all errors without re-throwing cancellation signals
- Mixing sync and async paths non-uniformly — inconsistent code paths where some resolve sync and others async, causing Zalgo-style bugs
- Object property iteration order in async code — assuming insertion-order iteration is safe when async ops modify the object concurrently
- Using `Array.forEach` with async callbacks — `forEach` does not await, leading to unintended parallelism and uncaught rejections
- Ignoring rejected promises — no `.catch()` and no `try/catch` around await
- Sequential `await` in a loop when parallel execution is possible — using `for...of await` instead of `Promise.all`
- Additional anti-patterns covering misuse of `setTimeout` as a synchronization mechanism, wrong error handling in `Promise.all`, mutating shared state across microtask boundaries

### race-conditions (44 documents)

Specific scenarios where concurrent execution produces incorrect results due to ordering or timing issues. Topics include:

- Shared variable modified inside `setTimeout` — two timers racing to read-modify-write the same variable
- Concurrent write to the same array — multiple async ops pushing to a shared array without coordination
- Closure capturing a mutable loop variable — classic `var i` in a for-loop with async callbacks
- Fetch deduplication race — two identical fetch calls issued before either completes, leading to duplicate processing
- Concurrent session token validation — two requests validating and renewing a token simultaneously
- Concurrent autocomplete cancellation — user types fast, earlier fetch resolves after later one and overwrites results
- Shared Worker state across tabs — multiple tabs sharing a Worker with shared mutable state
- Generator coroutine shared state — two coroutines interleaved by the scheduler modifying shared variables
- Async event handler memory leak pattern — event listener added inside an async function re-added on every invocation
- Async middleware execution order — Express/Koa-style middleware where async next() is called in wrong order
- TOCTOU (time-of-check/time-of-use) in async code — checking a condition then acting on it after an await that invalidates the check
- Additional scenarios covering IndexedDB transaction races, WebSocket message ordering, Service Worker cache stampede, concurrent localStorage access across tabs

---

## How BM25 Uses This Knowledge Base

### Server Startup

```
FastAPI starts
  → load knowledge_base.json (250 docs)
  → buildIndex(docs)
      → for each doc: tokenize(content) → lowercase → remove stopwords → store term frequencies
      → compute IDF for all terms across corpus
      → BM25 index held in RAM
```

### Per-Request Flow (`POST /api/v1/ai/analyze`)

```
Incoming request {code, language, user_id}
  → AI1 AST preprocessor extracts keywords from code
  → search(keywords, topK=3)
      → BM25 scores all 250 docs against query
      → returns top 3 docs by relevance score
  → 3 docs injected into LLM prompt as RELEVANT PATTERNS context
  → LLM generates suggestions grounded in retrieved docs
```

The BM25 retrieval ensures the LLM sees specific, relevant documentation for whatever concurrency pattern or anti-pattern is present in the submitted code, rather than relying on its general training data alone.

---

## How to Add More Documents

The file is a flat JSON array. To add new documents:

1. Open `ai2-knowledge-base/knowledge_base.json`.
2. Append new objects at the end of the array.
3. Increment the ID: the next document after `js-250` should be `js-251`, then `js-252`, etc.
4. All 6 fields are required: `id`, `title`, `content`, `language`, `category`, `source`, `url`.
5. `language` must be `"javascript"` (or extend to other languages if the pipeline is updated).
6. `category` must be one of: `"patterns"`, `"anti-patterns"`, `"race-conditions"`.
7. Restart the FastAPI server so `buildIndex` runs again with the new docs.

Example new document:

```json
{
  "id": "js-251",
  "title": "navigator.locks.request — Web Locks API Basic Usage",
  "content": "...",
  "language": "javascript",
  "category": "patterns",
  "source": "MDN Web Docs",
  "url": "https://developer.mozilla.org/en-US/docs/Web/API/LockManager/request"
}
```

---

## Status

**COMPLETE** — Task AI2-01 is done. The `knowledge_base.json` file contains all 250 documents and is ready for consumption by the BM25 indexing module (AI2-02).
