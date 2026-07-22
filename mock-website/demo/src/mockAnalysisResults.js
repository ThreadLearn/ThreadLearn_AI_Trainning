// Pre-computed analysis results for each sample in mockCases.js.
// Mirrors the real AI2 pipeline output schema (Issue, DocUsed, pipeline steps)
// so the demo UI renders identically to the live backend — no server needed.

const AST_FLOW = [
  "1. Parse code into AST tree (esprima)",
  "2. Walk nodes to extract Identifier tokens",
  "3. Filter out JS stopwords (if, for, async...)",
  "4. Retain unique keywords for search",
];

function step(stage, label, extra = {}) {
  return { stage, status: "done", label, ...extra };
}

// index matches LIVE_SAMPLES order in mockCases.js
export const MOCK_RESULTS = [
  // 0 — basic: setTimeout with var
  {
    pipeline: [
      step("race_detector", "Race detector: 1 pattern(s) found", {
        found: ["closure_loop_var"],
        detections: [{ pattern_id: "closure_loop_var", line_range: "2-4", severity: "high", description: "var captured by reference in loop callback" }],
      }),
      step("ast", "AST keywords: setTimeout console log", { keywords: "setTimeout console log", process_flow: AST_FLOW }),
      step("bm25", "BM25: 1 doc(s) retrieved", { docs: [{ title: "Closure Loop Variable [patterns]", score: 8.42, category: "patterns" }] }),
      step("prompt", "Prompt ready — 612 chars", { chars: 612 }),
      step("llm", "Model returned 1 issue(s), each with its own fix", { severity_counts: { high: 1, medium: 0, low: 0 } }),
    ],
    issues: [{
      pattern_id: "closure_loop_var",
      line_range: "2-4",
      severity: "high",
      description: "The var loop variable is captured by reference — every setTimeout callback shares the same binding, so all three fire with i already at its final value (3).",
      fix: "```javascript\nfor (let i = 0; i < 3; i++) {\n  setTimeout(function() {\n    console.log(i); // prints 0, 1, 2\n  }, 100);\n}\n```",
    }],
    docsUsed: [{ id: "js-014", title: "Closure Loop Variable [patterns]", category: "patterns" }],
    patternsChecked: 18,
  },

  // 1 — basic: async without try/catch
  {
    pipeline: [
      step("race_detector", "Race detector: 1 pattern(s) found", {
        found: ["unhandled_rejection"],
        detections: [{ pattern_id: "unhandled_rejection", line_range: "2-4", severity: "medium", description: "async function has no try/catch around await" }],
      }),
      step("ast", "AST keywords: loadUser db findUser user", { keywords: "loadUser db findUser user", process_flow: AST_FLOW }),
      step("bm25", "BM25: 1 doc(s) retrieved", { docs: [{ title: "Unhandled Promise Rejection [anti-patterns]", score: 7.9, category: "anti-patterns" }] }),
      step("prompt", "Prompt ready — 588 chars", { chars: 588 }),
      step("llm", "Model returned 1 issue(s), each with its own fix", { severity_counts: { high: 0, medium: 1, low: 0 } }),
    ],
    issues: [{
      pattern_id: "unhandled_rejection",
      line_range: "2-4",
      severity: "medium",
      description: "If db.findUser rejects, the promise rejection is never caught — this crashes the process on Node.js (unhandled rejection).",
      fix: "```javascript\nasync function loadUser(id) {\n  try {\n    const user = await db.findUser(id);\n    return user;\n  } catch (err) {\n    console.error('loadUser failed:', err);\n    throw err;\n  }\n}\n```",
    }],
    docsUsed: [{ id: "js-088", title: "Unhandled Promise Rejection [anti-patterns]", category: "anti-patterns" }],
    patternsChecked: 18,
  },

  // 2 — basic: callback missing return
  {
    pipeline: [
      step("race_detector", "Race detector: 1 pattern(s) found", {
        found: ["double_callback"],
        detections: [{ pattern_id: "double_callback", line_range: "2-5", severity: "high", description: "callback called twice on error path (missing return)" }],
      }),
      step("ast", "AST keywords: getUser db find callback", { keywords: "getUser db find callback", process_flow: AST_FLOW }),
      step("bm25", "BM25: 1 doc(s) retrieved", { docs: [{ title: "Double Callback Invocation [anti-patterns]", score: 8.1, category: "anti-patterns" }] }),
      step("prompt", "Prompt ready — 601 chars", { chars: 601 }),
      step("llm", "Model returned 1 issue(s), each with its own fix", { severity_counts: { high: 1, medium: 0, low: 0 } }),
    ],
    issues: [{
      pattern_id: "double_callback",
      line_range: "2-5",
      severity: "high",
      description: "When err is truthy, callback(err) runs but the function keeps executing and calls callback(null, user) right after — the caller's callback fires twice.",
      fix: "```javascript\nfunction getUser(id, callback) {\n  db.find(id, function(err, user) {\n    if (err) return callback(err); // return added\n    callback(null, user);\n  });\n}\n```",
    }],
    docsUsed: [{ id: "js-041", title: "Double Callback Invocation [anti-patterns]", category: "anti-patterns" }],
    patternsChecked: 18,
  },

  // 3 — basic: 3 sequential independent awaits
  {
    pipeline: [
      step("race_detector", "Race detector: 1 pattern(s) found", {
        found: ["sequential_awaits"],
        detections: [{ pattern_id: "sequential_awaits", line_range: "2-4", severity: "medium", description: "independent awaits execute sequentially instead of in parallel" }],
      }),
      step("ast", "AST keywords: getProfile db users orders reviews", { keywords: "getProfile db users orders reviews", process_flow: AST_FLOW }),
      step("bm25", "BM25: 1 doc(s) retrieved", { docs: [{ title: "Promise.all Pattern — Parallel Execution [patterns]", score: 9.0, category: "patterns" }] }),
      step("prompt", "Prompt ready — 634 chars", { chars: 634 }),
      step("llm", "Model returned 1 issue(s), each with its own fix", { severity_counts: { high: 0, medium: 1, low: 0 } }),
    ],
    issues: [{
      pattern_id: "sequential_awaits",
      line_range: "2-4",
      severity: "medium",
      description: "user, orders, and reviews don't depend on each other, but each await blocks the next — this triples the total latency versus running them concurrently.",
      fix: "```javascript\nasync function getProfile(userId) {\n  const [user, orders, reviews] = await Promise.all([\n    db.users.findById(userId),\n    db.orders.find(userId),\n    db.reviews.find(userId),\n  ]);\n  return { user, orders, reviews };\n}\n```",
    }],
    docsUsed: [{ id: "js-002", title: "Promise.all Pattern — Parallel Execution [patterns]", category: "patterns" }],
    patternsChecked: 18,
  },

  // 4 — race_condition: db stock decrement
  {
    pipeline: [
      step("race_detector", "Race detector: 1 pattern(s) found", {
        found: ["counter_no_atomic"],
        detections: [{ pattern_id: "counter_no_atomic", line_range: "2-7", severity: "high", description: "non-atomic read-modify-write on shared stock counter" }],
      }),
      step("ast", "AST keywords: purchaseItem db getStock setStock createOrder", { keywords: "purchaseItem db getStock setStock createOrder", process_flow: AST_FLOW }),
      step("bm25", "BM25: 1 doc(s) retrieved", { docs: [{ title: "Atomic Database Operations [patterns]", score: 8.7, category: "patterns" }] }),
      step("prompt", "Prompt ready — 701 chars", { chars: 701 }),
      step("llm", "Model returned 1 issue(s), each with its own fix", { severity_counts: { high: 1, medium: 0, low: 0 } }),
    ],
    issues: [{
      pattern_id: "counter_no_atomic",
      line_range: "2-7",
      severity: "high",
      description: "Two concurrent requests can both read stock=1 before either writes — both proceed to create an order, oversell the item, and leave stock at 0 instead of -1.",
      fix: "```javascript\nasync function purchaseItem(productId, userId) {\n  // Atomic conditional decrement — fails if stock would go negative\n  const result = await db.decrementStockIfPositive(productId);\n  if (!result.success) throw new Error('Out of stock');\n\n  await db.createOrder({ productId, userId });\n}\n```",
    }],
    docsUsed: [{ id: "js-race-019", title: "Atomic Database Operations [patterns]", category: "patterns" }],
    patternsChecked: 18,
  },

  // 5 — event_loop_blocking: readFileSync in loop
  {
    pipeline: [
      step("race_detector", "Race detector: 1 pattern(s) found", {
        found: ["sync_io_blocking"],
        detections: [{ pattern_id: "sync_io_blocking", line_range: "5-8", severity: "high", description: "synchronous file I/O inside async route handler" }],
      }),
      step("ast", "AST keywords: app get config files readFileSync JSON parse", { keywords: "app get config files readFileSync JSON parse", process_flow: AST_FLOW }),
      step("bm25", "BM25: 1 doc(s) retrieved", { docs: [{ title: "Event Loop Blocking — Sync I/O [anti-patterns]", score: 8.3, category: "anti-patterns" }] }),
      step("prompt", "Prompt ready — 668 chars", { chars: 668 }),
      step("llm", "Model returned 1 issue(s), each with its own fix", { severity_counts: { high: 1, medium: 0, low: 0 } }),
    ],
    issues: [{
      pattern_id: "sync_io_blocking",
      line_range: "5-8",
      severity: "high",
      description: "fs.readFileSync blocks Node's single event loop thread — every other request (health checks, other users) stalls until all 3 files finish reading.",
      fix: "```javascript\nconst fs = require('fs').promises;\n\napp.get('/config', async (req, res) => {\n  const files = ['db.json', 'cache.json', 'auth.json'];\n  const entries = await Promise.all(\n    files.map(async f => [f, JSON.parse(await fs.readFile(`/config/${f}`))])\n  );\n  res.json(Object.fromEntries(entries));\n});\n```",
    }],
    docsUsed: [{ id: "js-092", title: "Event Loop Blocking — Sync I/O [anti-patterns]", category: "anti-patterns" }],
    patternsChecked: 18,
  },

  // 6 — zalgo: sync/async mixed callback
  {
    pipeline: [
      step("race_detector", "Race detector: 1 pattern(s) found", {
        found: ["zalgo"],
        detections: [{ pattern_id: "zalgo", line_range: "2-9", severity: "medium", description: "callback resolves synchronously on cache hit, asynchronously on miss" }],
      }),
      step("ast", "AST keywords: getUserData cache db findUser callback", { keywords: "getUserData cache db findUser callback", process_flow: AST_FLOW }),
      step("bm25", "BM25: 1 doc(s) retrieved", { docs: [{ title: "Zalgo — Inconsistent Async Callback Timing [anti-patterns]", score: 8.6, category: "anti-patterns" }] }),
      step("prompt", "Prompt ready — 742 chars", { chars: 742 }),
      step("llm", "Model returned 1 issue(s), each with its own fix", { severity_counts: { high: 0, medium: 1, low: 0 } }),
    ],
    issues: [{
      pattern_id: "zalgo",
      line_range: "2-9",
      severity: "medium",
      description: "Callers cannot predict whether the callback fires before or after the next line of code runs, since the same function is sometimes sync (cache hit) and sometimes async (cache miss).",
      fix: "```javascript\nfunction getUserData(userId, callback) {\n  if (cache.has(userId)) {\n    // Force async boundary so behavior is always consistent\n    return process.nextTick(() => callback(null, cache.get(userId)));\n  }\n  db.findUser(userId, function(err, user) {\n    if (err) return callback(err);\n    cache.set(userId, user);\n    callback(null, user);\n  });\n}\n```",
    }],
    docsUsed: [{ id: "js-anti-057", title: "Zalgo — Inconsistent Async Callback Timing [anti-patterns]", category: "anti-patterns" }],
    patternsChecked: 18,
  },

  // 7 — resource_exhaustion: Promise.all unlimited
  {
    pipeline: [
      step("race_detector", "Race detector: 1 pattern(s) found", {
        found: ["resource_exhaustion"],
        detections: [{ pattern_id: "resource_exhaustion", line_range: "2-9", severity: "high", description: "unbounded Promise.all fires all items concurrently with no limit" }],
      }),
      step("ast", "AST keywords: sendBulkEmails userIds db users emailService send", { keywords: "sendBulkEmails userIds db users emailService send", process_flow: AST_FLOW }),
      step("bm25", "BM25: 1 doc(s) retrieved", { docs: [{ title: "Concurrency Limiting with p-limit [patterns]", score: 8.9, category: "patterns" }] }),
      step("prompt", "Prompt ready — 719 chars", { chars: 719 }),
      step("llm", "Model returned 1 issue(s), each with its own fix", { severity_counts: { high: 1, medium: 0, low: 0 } }),
    ],
    issues: [{
      pattern_id: "resource_exhaustion",
      line_range: "2-9",
      severity: "high",
      description: "With 10,000 user IDs, this fires 10,000 concurrent DB queries and HTTP calls at once — exhausting the DB connection pool and process memory, likely crashing the service.",
      fix: "```javascript\nimport pLimit from 'p-limit';\nconst limit = pLimit(20); // max 20 concurrent operations\n\nasync function sendBulkEmails(userIds) {\n  const users = await Promise.all(\n    userIds.map(id => limit(() => db.users.findById(id)))\n  );\n  await Promise.all(\n    users.map(user => limit(() => emailService.send(user.email, 'Hello!')))\n  );\n}\n```",
    }],
    docsUsed: [{ id: "js-patt-103", title: "Concurrency Limiting with p-limit [patterns]", category: "patterns" }],
    patternsChecked: 18,
  },

  // 8 — callback_hell: nested 4 levels
  {
    pipeline: [
      step("race_detector", "Race detector: 1 pattern(s) found", {
        found: ["callback_hell"],
        detections: [{ pattern_id: "callback_hell", line_range: "2-13", severity: "medium", description: "4 levels of nested callbacks (pyramid of doom)" }],
      }),
      step("ast", "AST keywords: processOrder db getOrder getUser payment charge email send", { keywords: "processOrder db getOrder getUser payment charge email send", process_flow: AST_FLOW }),
      step("bm25", "BM25: 1 doc(s) retrieved", { docs: [{ title: "Callback Hell — Flatten with async/await [anti-patterns]", score: 8.5, category: "anti-patterns" }] }),
      step("prompt", "Prompt ready — 812 chars", { chars: 812 }),
      step("llm", "Model returned 1 issue(s), each with its own fix", { severity_counts: { high: 0, medium: 1, low: 0 } }),
    ],
    issues: [{
      pattern_id: "callback_hell",
      line_range: "2-13",
      severity: "medium",
      description: "Four nested error-handling callbacks make control flow hard to follow and error handling repetitive — each level needs its own if (err) return callback(err) guard.",
      fix: "```javascript\nasync function processOrder(orderId) {\n  const order = await db.getOrder(orderId);\n  const user = await db.getUser(order.userId);\n  const charge = await payment.charge(user.card, order.total);\n  await email.send(user.email, 'Order confirmed');\n  return { order, charge };\n}\n```",
    }],
    docsUsed: [{ id: "js-anti-076", title: "Callback Hell — Flatten with async/await [anti-patterns]", category: "anti-patterns" }],
    patternsChecked: 18,
  },

  // 9 — missing_error_handler: stream pipe
  {
    pipeline: [
      step("race_detector", "Race detector: 1 pattern(s) found", {
        found: ["buffer_leak"],
        detections: [{ pattern_id: "buffer_leak", line_range: "5-8", severity: "high", description: "stream chain missing error handlers" }],
      }),
      step("ast", "AST keywords: createReadStream zlib createGzip pipe res", { keywords: "createReadStream zlib createGzip pipe res", process_flow: AST_FLOW }),
      step("bm25", "BM25: 1 doc(s) retrieved", { docs: [{ title: "Stream Error Handling [patterns]", score: 8.0, category: "patterns" }] }),
      step("prompt", "Prompt ready — 655 chars", { chars: 655 }),
      step("llm", "Model returned 1 issue(s), each with its own fix", { severity_counts: { high: 1, medium: 0, low: 0 } }),
    ],
    issues: [{
      pattern_id: "buffer_leak",
      line_range: "5-8",
      severity: "high",
      description: "If the file doesn't exist or the client disconnects mid-download, the stream chain has no error handler — the error is unhandled and can crash the process, leaking file descriptors.",
      fix: "```javascript\napp.get('/download/:file', (req, res) => {\n  const readStream = fs.createReadStream(`/data/${req.params.file}`);\n  const gzip = zlib.createGzip();\n\n  readStream.on('error', err => res.status(404).end());\n  gzip.on('error', err => res.destroy(err));\n\n  readStream.pipe(gzip).pipe(res);\n});\n```",
    }],
    docsUsed: [{ id: "js-patt-061", title: "Stream Error Handling [patterns]", category: "patterns" }],
    patternsChecked: 18,
  },

  // 10 — singleton_race: lazy init shared state
  {
    pipeline: [
      step("race_detector", "Race detector: 1 pattern(s) found", {
        found: ["promise_no_await"],
        detections: [{ pattern_id: "promise_no_await", line_range: "3-8", severity: "high", description: "lazy singleton check-then-act race on shared connection variable" }],
      }),
      step("ast", "AST keywords: getConnection dbConnection db connect", { keywords: "getConnection dbConnection db connect", process_flow: AST_FLOW }),
      step("bm25", "BM25: 1 doc(s) retrieved", { docs: [{ title: "Singleton Lazy Initialization Race [race-conditions]", score: 8.75, category: "race-conditions" }] }),
      step("prompt", "Prompt ready — 693 chars", { chars: 693 }),
      step("llm", "Model returned 1 issue(s), each with its own fix", { severity_counts: { high: 1, medium: 0, low: 0 } }),
    ],
    issues: [{
      pattern_id: "promise_no_await",
      line_range: "3-8",
      severity: "high",
      description: "Two concurrent requests can both see dbConnection === null before either finishes await db.connect() — both create a separate connection, and one is silently discarded.",
      fix: "```javascript\nlet connectionPromise = null;\n\nfunction getConnection() {\n  // Cache the PROMISE, not the resolved value — concurrent\n  // callers all await the same in-flight connect() call.\n  if (!connectionPromise) {\n    connectionPromise = db.connect();\n  }\n  return connectionPromise;\n}\n```",
    }],
    docsUsed: [{ id: "js-race-032", title: "Singleton Lazy Initialization Race [race-conditions]", category: "race-conditions" }],
    patternsChecked: 18,
  },

  // 11 — event_loop_ordering: nextTick vs setTimeout
  {
    pipeline: [
      step("race_detector", "Race detector: 1 pattern(s) found", {
        found: ["zalgo"],
        detections: [{ pattern_id: "zalgo", line_range: "6-17", severity: "high", description: "process.nextTick assumed to run after setTimeout, but nextTick always runs first" }],
      }),
      step("ast", "AST keywords: DataLoader data load setTimeout nextTick callback", { keywords: "DataLoader data load setTimeout nextTick callback", process_flow: AST_FLOW }),
      step("bm25", "BM25: 1 doc(s) retrieved", { docs: [{ title: "Event Loop Ordering — nextTick vs setTimeout [patterns]", score: 8.55, category: "patterns" }] }),
      step("prompt", "Prompt ready — 758 chars", { chars: 758 }),
      step("llm", "Model returned 1 issue(s), each with its own fix", { severity_counts: { high: 1, medium: 0, low: 0 } }),
    ],
    issues: [{
      pattern_id: "zalgo",
      line_range: "6-17",
      severity: "high",
      description: "process.nextTick always fires before any setTimeout callback, even setTimeout(fn, 0) — so getData's callback runs before load()'s setTimeout has set this.data, and the caller reads null.",
      fix: "```javascript\nclass DataLoader {\n  constructor() {\n    this.data = null;\n    this.ready = this.load();\n  }\n\n  async load() {\n    this.data = await new Promise(resolve =>\n      setTimeout(() => resolve({ users: [1, 2, 3] }), 0)\n    );\n  }\n\n  async getData(callback) {\n    await this.ready; // wait for load() to actually finish\n    callback(this.data);\n  }\n}\n```",
    }],
    docsUsed: [{ id: "js-patt-118", title: "Event Loop Ordering — nextTick vs setTimeout [patterns]", category: "patterns" }],
    patternsChecked: 18,
  },
];
