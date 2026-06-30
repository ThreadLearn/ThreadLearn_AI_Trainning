import json, pathlib, sys

KB_PATH = pathlib.Path(__file__).parent / "knowledge_base.json"

NEW_DOCS = [
    {
        "id": "js-patch-001",
        "title": "Singleton Promise Pattern: Cache the Promise, Not the Result",
        "content": (
            "A common race condition occurs when multiple concurrent callers each trigger an async "
            "operation before any result is cached. The fix is to cache the Promise object itself "
            "(not the resolved value), so all callers share the same in-flight request.\n\n"
            "BAD — race condition, multiple fetches launched:\n"
            "```javascript\n"
            "let cache = null;\n"
            "function getCache() {\n"
            "  if (!cache) fetchData().then(d => cache = d);\n"
            "  return cache; // returns null on concurrent calls!\n"
            "}\n"
            "```\n\n"
            "GOOD — singleton promise, only one fetch ever fires:\n"
            "```javascript\n"
            "let promise = null;\n"
            "function getCache() {\n"
            "  if (!promise) promise = fetchData();\n"
            "  return promise; // all callers await the same promise\n"
            "}\n"
            "```\n\n"
            "Key insight: Promises are reusable. Once created, they can be awaited by many consumers. "
            "Caching the Promise prevents duplicate side-effects (DB queries, network requests, file reads). "
            "Use this pattern for any initialisation that must run exactly once."
        ),
        "language": "javascript",
        "category": "race-condition",
        "source": "ThreadLearn Knowledge Base — Patch v2",
        "url": ""
    },
    {
        "id": "js-patch-002",
        "title": "Atomic File Append: fs.appendFile vs readFile+writeFile Race",
        "content": (
            "Combining fs.readFile + fs.writeFile is NOT atomic. Two concurrent callers can both "
            "read the same old content, then both write, causing one writer's data to be lost.\n\n"
            "BAD — read-then-write race condition:\n"
            "```javascript\n"
            "function appendLog(msg) {\n"
            "  fs.readFile('log.txt', 'utf8', (err, data) => {\n"
            "    fs.writeFile('log.txt', data + msg, () => {});\n"
            "  });\n"
            "}\n"
            "appendLog('A');\n"
            "appendLog('B'); // B reads before A writes → A's content lost!\n"
            "```\n\n"
            "GOOD — atomic OS-level append:\n"
            "```javascript\n"
            "const { promises: fs } = require('fs');\n"
            "async function appendLog(msg) {\n"
            "  await fs.appendFile('log.txt', msg + '\\n');\n"
            "}\n"
            "await Promise.all([appendLog('A'), appendLog('B')]); // both written safely\n"
            "```\n\n"
            "fs.appendFile() delegates to the OS open(O_APPEND) system call which is atomic at the "
            "kernel level — two concurrent appends will never overwrite each other. "
            "Always use appendFile for concurrent log/event writing."
        ),
        "language": "javascript",
        "category": "race-condition",
        "source": "ThreadLearn Knowledge Base — Patch v2",
        "url": ""
    },
    {
        "id": "js-patch-003",
        "title": "Double Callback Guard: Always 'return cb()' to Prevent Double Invocation",
        "content": (
            "In callback-style Node.js code, omitting 'return' before cb() causes the callback to be "
            "called multiple times when multiple exit branches exist (error + success path both execute).\n\n"
            "BAD — callback invoked twice when err is truthy:\n"
            "```javascript\n"
            "function getUser(id, cb) {\n"
            "  db.findById(id, (err, user) => {\n"
            "    if (err) cb(err);           // no return!\n"
            "    if (!user) cb(new Error('Not found')); // runs even after err\n"
            "    cb(null, user);             // runs even after err or not found\n"
            "  });\n"
            "}\n"
            "```\n\n"
            "GOOD — return before every cb() call:\n"
            "```javascript\n"
            "function getUser(id, cb) {\n"
            "  db.findById(id, (err, user) => {\n"
            "    if (err) return cb(err);\n"
            "    if (!user) return cb(new Error('Not found'));\n"
            "    return cb(null, user);\n"
            "  });\n"
            "}\n"
            "```\n\n"
            "Rule: Every code path inside an async callback MUST end with 'return cb(...)'. "
            "Do NOT convert to async/await just to fix this — 'return cb()' is the minimal correct fix."
        ),
        "language": "javascript",
        "category": "double-callback",
        "source": "ThreadLearn Knowledge Base — Patch v2",
        "url": ""
    },
    {
        "id": "js-patch-004",
        "title": "Zalgo Anti-Pattern: Use process.nextTick to Normalize Async Behavior",
        "content": (
            "The Zalgo anti-pattern occurs when a function sometimes calls its callback synchronously "
            "(cache hit) and sometimes asynchronously (cache miss). This inconsistency makes the "
            "function unreliable and order-dependent for callers.\n\n"
            "BAD — Zalgo: sync cb on cache hit, async on miss:\n"
            "```javascript\n"
            "const cache = {};\n"
            "function fetchObj(id, cb) {\n"
            "  if (cache[id]) return cb(cache[id]); // sync!\n"
            "  networkFetch(id, data => {\n"
            "    cache[id] = data;\n"
            "    cb(data); // async\n"
            "  });\n"
            "}\n"
            "```\n\n"
            "GOOD — always async using process.nextTick:\n"
            "```javascript\n"
            "const cache = {};\n"
            "function fetchObj(id, cb) {\n"
            "  if (cache[id]) {\n"
            "    return process.nextTick(() => cb(null, cache[id])); // defer to next tick\n"
            "  }\n"
            "  networkFetch(id, (err, data) => {\n"
            "    if (err) return cb(err);\n"
            "    cache[id] = data;\n"
            "    cb(null, data);\n"
            "  });\n"
            "}\n"
            "```\n\n"
            "process.nextTick() defers execution to the next iteration of the event loop, making "
            "the callback always async. This ensures callers can always set up listeners or state "
            "before the callback fires. Use nextTick (not setTimeout/setImmediate) for minimal overhead."
        ),
        "language": "javascript",
        "category": "zalgo",
        "source": "ThreadLearn Knowledge Base — Patch v2",
        "url": ""
    },
    {
        "id": "js-patch-005",
        "title": "Stream Buffer Leak: Cleanup Readable Streams on Client Disconnect",
        "content": (
            "When piping a Readable stream to an HTTP response, if the client disconnects early, "
            "the stream keeps reading and buffering data in memory — causing a buffer/memory leak. "
            "Always handle stream errors and destroy the stream on disconnect.\n\n"
            "BAD — stream keeps running after client disconnect:\n"
            "```javascript\n"
            "function streamData(req, res) {\n"
            "  const rs = fs.createReadStream('file.mp4');\n"
            "  rs.on('end', () => res.end());\n"
            "  rs.on('error', err => res.status(500).send(err.message));\n"
            "  // No cleanup on client disconnect!\n"
            "}\n"
            "```\n\n"
            "GOOD — destroy stream when client disconnects:\n"
            "```javascript\n"
            "function streamData(req, res) {\n"
            "  const rs = fs.createReadStream('file.mp4');\n"
            "  rs.pipe(res);\n"
            "  rs.on('error', err => {\n"
            "    if (!res.headersSent) res.status(500).end();\n"
            "  });\n"
            "  req.on('close', () => rs.destroy()); // client disconnected: stop streaming\n"
            "  res.on('finish', () => rs.destroy()); // response done: cleanup\n"
            "}\n"
            "```\n\n"
            "Key points:\n"
            "1. rs.pipe(res) automatically handles backpressure and end events.\n"
            "2. req.on('close') fires when client drops connection — always destroy() the source stream.\n"
            "3. rs.on('error') must be handled or Node.js will throw an uncaught exception.\n"
            "4. Check res.headersSent before writing error responses to avoid 'headers already sent' errors."
        ),
        "language": "javascript",
        "category": "buffer-leak",
        "source": "ThreadLearn Knowledge Base — Patch v2",
        "url": ""
    }
]

def main():
    with open(KB_PATH, "r", encoding="utf-8") as f:
        kb = json.load(f)

    existing_ids = {doc["id"] for doc in kb}
    added = 0
    for doc in NEW_DOCS:
        if doc["id"] not in existing_ids:
            kb.append(doc)
            added += 1
            print(f"  [+] Added: {doc['id']} — {doc['title']}")
        else:
            print(f"  [=] Already exists: {doc['id']}")

    with open(KB_PATH, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {added} documents added. Total: {len(kb)}")

if __name__ == "__main__":
    main()
