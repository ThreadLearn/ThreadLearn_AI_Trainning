import json
import os

new_pairs = [
    # Event Loop Blocking
    {
        "input": "const crypto = require('crypto');\nconst hashPasswords = (users) => {\n  users.forEach(user => {\n    // Bug: Synchronous crypto operation blocks event loop for all users\n    user.hash = crypto.pbkdf2Sync(user.password, 'salt', 100000, 64, 'sha512');\n  });\n};",
        "output": "// Fix: Use asynchronous crypto to prevent event loop blocking.\nconst crypto = require('crypto');\nconst hashPasswords = async (users) => {\n  const promises = users.map(user => \n    new Promise((resolve, reject) => {\n      crypto.pbkdf2(user.password, 'salt', 100000, 64, 'sha512', (err, derivedKey) => {\n        if (err) return reject(err);\n        user.hash = derivedKey;\n        resolve();\n      });\n    })\n  );\n  await Promise.all(promises);\n};"
    },
    {
        "input": "const processHugeArray = (arr) => {\n  // Bug: huge synchronous loop blocks event loop, stopping server from handling requests\n  for (let i = 0; i < arr.length; i++) {\n    performHeavyComputation(arr[i]);\n  }\n};",
        "output": "// Fix: Chunk the array processing and use setImmediate to yield to the event loop.\nconst processHugeArray = async (arr) => {\n  for (let i = 0; i < arr.length; i++) {\n    performHeavyComputation(arr[i]);\n    if (i % 100 === 0) {\n      await new Promise(resolve => setImmediate(resolve));\n    }\n  }\n};"
    },
    # Streams / Buffer Leaks
    {
        "input": "const fs = require('fs');\nconst streamFile = (req, res) => {\n  const readStream = fs.createReadStream('hugeFile.mp4');\n  readStream.pipe(res);\n  // Bug: if response closes prematurely, readStream stays open causing memory/file descriptor leak\n};",
        "output": "// Fix: Handle response close/error events to destroy the read stream.\nconst fs = require('fs');\nconst streamFile = (req, res) => {\n  const readStream = fs.createReadStream('hugeFile.mp4');\n  readStream.pipe(res);\n  res.on('close', () => readStream.destroy());\n  res.on('error', () => readStream.destroy());\n};"
    },
    {
        "input": "const downloadAndProcess = (url) => {\n  const req = http.get(url, (res) => {\n    let data = '';\n    res.on('data', chunk => data += chunk);\n    res.on('end', () => processData(data));\n  });\n  // Bug: does not handle req error event, crashes the app\n};",
        "output": "// Fix: Attach error listener to the request object to prevent UnhandledPromiseRejection or crash.\nconst downloadAndProcess = (url) => {\n  const req = http.get(url, (res) => {\n    let data = '';\n    res.on('data', chunk => data += chunk);\n    res.on('end', () => processData(data));\n  });\n  req.on('error', (err) => console.error('Download error:', err));\n};"
    },
    # EventEmitter Chaos (Memory Leaks)
    {
        "input": "const db = require('./db');\nconst setupUser = (userId) => {\n  // Bug: Adding a new listener every time setupUser is called causes MaxListenersExceededWarning\n  db.on('connected', () => {\n    initializeProfile(userId);\n  });\n};",
        "output": "// Fix: Use .once instead of .on, or check if listener already exists, to avoid listener leaks.\nconst db = require('./db');\nconst setupUser = (userId) => {\n  db.once('connected', () => {\n    initializeProfile(userId);\n  });\n};"
    },
    {
        "input": "class Worker extends EventEmitter {\n  start() {\n    this.on('task', (data) => {\n      processTask(data).then(() => this.emit('task', nextTask)); // Bug: potential infinite loop / stack overflow if synchronous\n    });\n  }\n}",
        "output": "// Fix: Use setImmediate or nextTick when recursively emitting events to prevent call stack overflow.\nclass Worker extends EventEmitter {\n  start() {\n    this.on('task', (data) => {\n      processTask(data).then(() => {\n        setImmediate(() => this.emit('task', nextTask));\n      });\n    });\n  }\n};"
    }
]

# Read the original 20 pairs
old_pairs = []
try:
    with open('training/data/raw/bugsjs_batch.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                obj = json.loads(line)
                old_pairs.append({
                    "input": obj["prompt"],
                    "output": obj["completion"]
                })
except Exception as e:
    print(f"Failed to read batch: {e}")

all_pairs = old_pairs + new_pairs

with open('training/data/raw/bugsjs_raw.json', 'w', encoding='utf-8') as f:
    json.dump(all_pairs, f, indent=2, ensure_ascii=False)

print(f"Successfully generated bugsjs_raw.json with {len(all_pairs)} pairs.")
