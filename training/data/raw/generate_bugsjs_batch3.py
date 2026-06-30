import json

new_pairs = [
    # 1. Resource Exhaustion (EMFILE)
    {
        "input": "const fs = require('fs').promises;\nconst readAllFiles = async (files) => {\n  // Bug: Opening 10000 files concurrently crashes with EMFILE\n  return await Promise.all(files.map(f => fs.readFile(f, 'utf8')));\n};",
        "output": "// Fix: Use chunking or a concurrency limiter like p-limit to avoid EMFILE.\nconst fs = require('fs').promises;\nconst readAllFiles = async (files) => {\n  const results = [];\n  const chunkSize = 100;\n  for (let i = 0; i < files.length; i += chunkSize) {\n    const chunk = files.slice(i, i + chunkSize);\n    const chunkResults = await Promise.all(chunk.map(f => fs.readFile(f, 'utf8')));\n    results.push(...chunkResults);\n  }\n  return results;\n};"
    },
    {
        "input": "const fetchAll = async (urls) => {\n  // Bug: Too many concurrent requests exhaust sockets and crash\n  const responses = await Promise.all(urls.map(url => fetch(url)));\n  return responses.map(r => r.json());\n};",
        "output": "// Fix: Process requests sequentially or use a library to limit concurrency.\nconst fetchAll = async (urls) => {\n  const results = [];\n  for (const url of urls) {\n    const response = await fetch(url);\n    results.push(await response.json());\n  }\n  return results;\n};"
    },
    # 2. Double Callback Execution
    {
        "input": "const verifyUser = (req, res, next) => {\n  db.findUser(req.body.id, (err, user) => {\n    if (err) next(err); // Bug: Missing return, code continues executing\n    if (!user) next(new Error('Not found')); // Bug: Missing return\n    req.user = user;\n    next();\n  });\n};",
        "output": "// Fix: Added return statements to prevent double callback execution and 'headers already sent' errors.\nconst verifyUser = (req, res, next) => {\n  db.findUser(req.body.id, (err, user) => {\n    if (err) return next(err);\n    if (!user) return next(new Error('Not found'));\n    req.user = user;\n    next();\n  });\n};"
    },
    {
        "input": "const readFileData = (path, cb) => {\n  fs.readFile(path, (err, data) => {\n    if (err) cb(err);\n    const parsed = JSON.parse(data); // Will crash if err occurs\n    cb(null, parsed);\n  });\n};",
        "output": "// Fix: Added return to stop execution on error, and wrapped JSON.parse in try-catch.\nconst readFileData = (path, cb) => {\n  fs.readFile(path, (err, data) => {\n    if (err) return cb(err);\n    try {\n      const parsed = JSON.parse(data);\n      cb(null, parsed);\n    } catch (e) {\n      cb(e);\n    }\n  });\n};"
    },
    # 3. Context Loss ('this' Binding)
    {
        "input": "class DataFetcher {\n  constructor() {\n    this.url = '/api/data';\n  }\n  fetchData() {\n    request(this.url, function(err, res) {\n      // Bug: 'this' is undefined inside standard function callback\n      this.process(res);\n    });\n  }\n  process(res) { console.log(res); }\n}",
        "output": "// Fix: Used arrow function to preserve the lexical 'this' context.\nclass DataFetcher {\n  constructor() {\n    this.url = '/api/data';\n  }\n  fetchData() {\n    request(this.url, (err, res) => {\n      if (err) return;\n      this.process(res);\n    });\n  }\n  process(res) { console.log(res); }\n}"
    },
    {
        "input": "const userProfile = {\n  name: 'Alice',\n  loadDeps: function() {\n    setTimeout(function() {\n      console.log(this.name + ' loaded'); // Bug: this.name is undefined\n    }, 100);\n  }\n};",
        "output": "// Fix: Use arrow function in setTimeout to bind 'this' correctly.\nconst userProfile = {\n  name: 'Alice',\n  loadDeps: function() {\n    setTimeout(() => {\n      console.log(this.name + ' loaded');\n    }, 100);\n  }\n};"
    },
    # 4. Macrotask vs Microtask Event Loop Ordering
    {
        "input": "const processFile = (file) => {\n  setTimeout(() => cleanup(file), 0); // Bug: cleanup happens before nextTick/Promise logic finishes in other parts\n  return fs.promises.readFile(file);\n};",
        "output": "// Fix: Use setImmediate or await to ensure cleanup happens strictly after processing.\nconst processFile = async (file) => {\n  try {\n    return await fs.promises.readFile(file);\n  } finally {\n    setImmediate(() => cleanup(file));\n  }\n};"
    },
    {
        "input": "let initialized = false;\nprocess.nextTick(() => { initialized = true; });\nsetTimeout(() => {\n  // Bug: Assume initialized is true, but event loop ordering might be tricky if heavily loaded\n  console.log(initialized);\n}, 0);",
        "output": "// Fix: Avoid mixing nextTick and setTimeout for dependent initialization logic. Use Promises instead.\nlet initialized = false;\nPromise.resolve().then(() => {\n  initialized = true;\n}).then(() => {\n  console.log(initialized);\n});"
    }
]

with open('training/data/raw/bugsjs_batch3.json', 'w', encoding='utf-8') as f:
    json.dump(new_pairs, f, indent=2, ensure_ascii=False)
