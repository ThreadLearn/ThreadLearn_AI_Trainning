// Static fake "analysis history" so the demo shows the History section and
// trend chart populated, exactly like a real user account with prior runs.
const now = Date.now();
const day = 24 * 60 * 60 * 1000;

export const MOCK_HISTORY = [
  {
    _id: 'h6', language: 'javascript', createdAt: new Date(now - 1 * day).toISOString(), cached: false,
    inputCode: "for (var i = 0; i < 3; i++) {\n  setTimeout(function() {\n    console.log(i);\n  }, 100);\n}",
    issues: [{ pattern_id: 'closure_loop_var', line_range: '2-4', severity: 'high', description: 'var loop variable captured by reference — all callbacks read the final value.', fix: '```javascript\nfor (let i = 0; i < 3; i++) {\n  setTimeout(() => console.log(i), 100);\n}\n```' }],
    docsUsed: [{ id: 'js-014', title: 'Closure Loop Variable', category: 'patterns' }],
    explanation: 'AI2 detected 1 issue using RAG retrieval from 1 knowledge-base document.',
    analyzeTimeMs: 3120,
  },
  {
    _id: 'h5', language: 'javascript', createdAt: new Date(now - 2 * day).toISOString(), cached: true,
    inputCode: 'async function loadUser(id) {\n  const user = await db.findUser(id);\n  return user;\n}',
    issues: [{ pattern_id: 'unhandled_rejection', line_range: '2-4', severity: 'medium', description: 'async function missing try/catch around await.', fix: '```javascript\nasync function loadUser(id) {\n  try {\n    return await db.findUser(id);\n  } catch (err) { throw err; }\n}\n```' }],
    docsUsed: [{ id: 'js-088', title: 'Unhandled Promise Rejection', category: 'anti-patterns' }],
    explanation: 'AI2 detected 1 issue using RAG retrieval from 1 knowledge-base document.',
    analyzeTimeMs: 2840,
  },
  {
    _id: 'h4', language: 'javascript', createdAt: new Date(now - 4 * day).toISOString(), cached: false,
    inputCode: 'async function purchaseItem(productId, userId) {\n  const stock = await db.getStock(productId);\n  await db.setStock(productId, stock - 1);\n}',
    issues: [
      { pattern_id: 'counter_no_atomic', line_range: '2-3', severity: 'high', description: 'Non-atomic read-modify-write allows overselling under concurrent requests.', fix: '```javascript\nawait db.decrementStockIfPositive(productId);\n```' },
      { pattern_id: 'promise_no_await', line_range: '3', severity: 'medium', description: 'setStock result not verified before proceeding.', fix: '```javascript\nconst ok = await db.setStock(productId, stock - 1);\nif (!ok) throw new Error("stock update failed");\n```' },
    ],
    docsUsed: [{ id: 'js-race-019', title: 'Atomic Database Operations', category: 'patterns' }, { id: 'js-race-020', title: 'Check-Then-Act Race', category: 'race-conditions' }],
    explanation: 'AI2 detected 2 issues using RAG retrieval from 2 knowledge-base documents.',
    analyzeTimeMs: 4310,
  },
  {
    _id: 'h3', language: 'javascript', createdAt: new Date(now - 6 * day).toISOString(), cached: false,
    inputCode: "app.get('/config', async (req, res) => {\n  const data = fs.readFileSync('/config/db.json');\n  res.json(JSON.parse(data));\n});",
    issues: [{ pattern_id: 'sync_io_blocking', line_range: '2', severity: 'high', description: 'Synchronous file I/O blocks the event loop for every other request.', fix: '```javascript\nconst data = await fs.promises.readFile("/config/db.json");\nres.json(JSON.parse(data));\n```' }],
    docsUsed: [{ id: 'js-092', title: 'Event Loop Blocking — Sync I/O', category: 'anti-patterns' }],
    explanation: 'AI2 detected 1 issue using RAG retrieval from 1 knowledge-base document.',
    analyzeTimeMs: 2955,
  },
  {
    _id: 'h2', language: 'javascript', createdAt: new Date(now - 9 * day).toISOString(), cached: false,
    inputCode: 'async function getProfile(userId) {\n  const user = await db.users.findById(userId);\n  const orders = await db.orders.find(userId);\n  return { user, orders };\n}',
    issues: [{ pattern_id: 'sequential_awaits', line_range: '2-3', severity: 'medium', description: 'Independent awaits run sequentially instead of in parallel.', fix: '```javascript\nconst [user, orders] = await Promise.all([\n  db.users.findById(userId),\n  db.orders.find(userId),\n]);\n```' }],
    docsUsed: [{ id: 'js-002', title: 'Promise.all Pattern', category: 'patterns' }],
    explanation: 'AI2 detected 1 issue using RAG retrieval from 1 knowledge-base document.',
    analyzeTimeMs: 2610,
  },
  {
    _id: 'h1', language: 'javascript', createdAt: new Date(now - 13 * day).toISOString(), cached: false,
    inputCode: 'function getUser(id, callback) {\n  db.find(id, function(err, user) {\n    if (err) callback(err);\n    callback(null, user);\n  });\n}',
    issues: [{ pattern_id: 'double_callback', line_range: '2-5', severity: 'high', description: 'callback() called twice on the error path — missing return.', fix: '```javascript\nfunction getUser(id, callback) {\n  db.find(id, function(err, user) {\n    if (err) return callback(err);\n    callback(null, user);\n  });\n}\n```' }],
    docsUsed: [{ id: 'js-041', title: 'Double Callback Invocation', category: 'anti-patterns' }],
    explanation: 'AI2 detected 1 issue using RAG retrieval from 1 knowledge-base document.',
    analyzeTimeMs: 3402,
  },
];
