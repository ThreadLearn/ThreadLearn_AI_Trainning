import json
import time
import sys
import os
import urllib.request

# Fix Unicode printing on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Thêm đường dẫn tới server để import rag_pipeline
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "server"))
from bm25_module import load_retriever
import rag_pipeline
import llm_client
from config import HF_TOKEN

REAL_WORLD_CASES = [
    {"id": "rw_01", "category": "Race Condition",
     "code": "fs.exists(filePath, function(exists) {\n  if (exists) {\n    fs.readFile(filePath, 'utf8', callback);\n  }\n});",
     "pass_keywords": ["readfile", "enoent", "atomic", "access", "toctou", "race"]},
    {"id": "rw_02", "category": "Double Callback",
     "code": "function query(sql, cb) {\n  connection.connect(function(err) {\n    if (err) cb(err);\n    connection.query(sql, function(err, results) {\n      cb(err, results);\n    });\n  });\n}",
     "pass_keywords": ["return cb", "return callback", "double", "called twice", "early return"]},
    {"id": "rw_03", "category": "Zalgo",
     "code": "function getData(key, callback) {\n  if (cache[key]) {\n    callback(null, cache[key]);\n  } else {\n    fetchFromDB(key, function(err, data) {\n      cache[key] = data;\n      callback(err, data);\n    });\n  }\n}",
     "pass_keywords": ["nexttick", "process.nexttick", "setimmediate", "zalgo", "async", "consistent"]},
    {"id": "rw_04", "category": "Event Loop Blocking",
     "code": "app.use(function(req, res, next) {\n  const result = [];\n  for (let i = 0; i < req.body.items.length; i++) {\n    result.push(heavyTransform(req.body.items[i]));\n  }\n  res.json(result);\n});",
     "pass_keywords": ["worker", "setimmediate", "async", "chunk", "promise", "block"]},
    {"id": "rw_05", "category": "Context Loss",
     "code": "class UserController {\n  constructor() { this.db = new Database(); }\n  async getUser(req, res) {\n    const user = await this.db.find(req.params.id);\n    res.json(user);\n  }\n}\nconst ctrl = new UserController();\napp.get('/user/:id', ctrl.getUser);",
     "pass_keywords": ["bind", "arrow", "this", ".bind(ctrl)", "=> ctrl"]},
    {"id": "rw_06", "category": "Resource Exhaustion",
     "code": "pool.connect(function(err, client, done) {\n  client.query('BEGIN', function(err) {\n    if (err) {\n      client.query('ROLLBACK', function(err) { done(); callback(err); });\n    }\n    client.query(sql, function(err, result) {\n      if (err) {\n        client.query('ROLLBACK', function(err) { done(); });\n        callback(err);\n      }\n      client.query('COMMIT', function(err) { done(); callback(null, result); });\n    });\n  });\n});",
     "pass_keywords": ["done()", "release", "return", "finally", "leak"]},
    {"id": "rw_07", "category": "Stream Leak",
     "code": "function serveFile(req, res) {\n  const readStream = fs.createReadStream(req.params.file);\n  const gzip = zlib.createGzip();\n  readStream.pipe(gzip).pipe(res);\n}",
     "pass_keywords": ["pipeline", "error", "destroy", "on('error'", "cleanup"]},
    {"id": "rw_08", "category": "Race Condition",
     "code": "app.post('/login', function(req, res, next) {\n  passport.authenticate('local', function(err, user) {\n    if (err) return next(err);\n    req.logIn(user, function(err) {\n      if (err) return next(err);\n      return res.redirect('/');\n    });\n  })(req, res, next);\n});",
     "pass_keywords": ["session", "atomic", "race", "concurrent", "await"]},
    {"id": "rw_09", "category": "Unhandled Rejection",
     "code": "co(function*() {\n  const conn = yield db.connect();\n  const result = yield conn.query(sql);\n  return result;\n}).then(function(result) {\n  res.json(result);\n});",
     "pass_keywords": ["catch", "try", "rejection", ".catch(", "error"]},
    {"id": "rw_10", "category": "Resource Exhaustion",
     "code": "const readStream = fs.createReadStream('huge-file.csv');\nreadStream.on('data', function(chunk) {\n  const parsed = parseCSVChunk(chunk);\n  writableDB.write(parsed);\n});",
     "pass_keywords": ["pause", "resume", "pipe", "backpressure", "drain", "highwatermark"]},
    {"id": "rw_11", "category": "Double Callback",
     "code": "function getWithTimeout(key, timeout, cb) {\n  const timer = setTimeout(function() {\n    cb(new Error('timeout'));\n  }, timeout);\n  client.get(key, function(err, data) {\n    cb(err, data);\n  });\n}",
     "pass_keywords": ["cleartimeout", "clearTimeout", "called twice", "return cb", "once"]},
    {"id": "rw_12", "category": "Sequential Awaits",
     "code": "async function getDashboard(userId) {\n  const user = await db.users.findById(userId);\n  const orders = await db.orders.findByUser(userId);\n  const notifications = await db.notifications.findByUser(userId);\n  return { user, orders, notifications };\n}",
     "pass_keywords": ["promise.all", "parallel", "concurrent", "Promise.all"]},
    {"id": "rw_13", "category": "Race Condition",
     "code": "queue.process(function(job, done) {\n  if (job.data.status === 'pending') {\n    job.data.status = 'processing';\n    processJob(job.data, function(err, result) {\n      done(err, result);\n    });\n  }\n});",
     "pass_keywords": ["atomic", "race", "lock", "redis", "transaction", "update"]},
    {"id": "rw_14", "category": "Callback Hell",
     "code": "fs.readFile(configPath, function(err, config) {\n  if (err) return callback(err);\n  db.connect(JSON.parse(config), function(err, conn) {\n    if (err) return callback(err);\n    conn.query(sql, function(err, rows) {\n      if (err) return callback(err);\n      rows.forEach(function(row) {\n        transform(row, function(err, result) {\n          results.push(result);\n        });\n      });\n      callback(null, results);\n    });\n  });\n});",
     "pass_keywords": ["async/await", "async await", "promise", "flatten", "await"]},
    {"id": "rw_15", "category": "Resource Exhaustion",
     "code": "async function notifyAllUsers(users) {\n  await Promise.all(\n    users.map(user =>\n      axios.post('/notify', { userId: user.id })\n    )\n  );\n}",
     "pass_keywords": ["limit", "chunk", "batch", "p-limit", "concurren", "slice"]},
    {"id": "rw_16", "category": "Event Loop Blocking",
     "code": "app.post('/register', function(req, res) {\n  const hash = crypto.pbkdf2Sync(\n    req.body.password,\n    req.body.username,\n    100000, 64, 'sha512'\n  );\n  db.users.create({ hash }, function(err) {\n    res.json({ ok: true });\n  });\n});",
     "pass_keywords": ["pbkdf2", "async", "worker", "promise", "block"]},
    {"id": "rw_17", "category": "Zalgo",
     "code": "function processItems(items, callback) {\n  if (items.length === 0) { callback(null, []); return; }\n  const item = items[0];\n  if (computedCache[item]) {\n    processItems(items.slice(1), function(err, rest) {\n      callback(null, [computedCache[item]].concat(rest));\n    });\n  } else {\n    asyncCompute(item, function(err, result) {\n      computedCache[item] = result;\n      processItems(items.slice(1), function(err, rest) {\n        callback(null, [result].concat(rest));\n      });\n    });\n  }\n}",
     "pass_keywords": ["nexttick", "setimmediate", "async", "consistent", "zalgo"]},
    {"id": "rw_18", "category": "Unhandled Rejection",
     "code": "app.get('/user/:id', async function(req, res) {\n  const user = await db.findUser(req.params.id);\n  res.json(user);\n});",
     "pass_keywords": ["try", "catch", "next(err", "rejection", ".catch"]},
    {"id": "rw_19", "category": "Race Condition",
     "code": "function createFileIfNotExists(filePath, content, callback) {\n  fs.access(filePath, fs.constants.F_OK, function(err) {\n    if (err) {\n      fs.writeFile(filePath, content, callback);\n    } else {\n      callback(null);\n    }\n  });\n}",
     "pass_keywords": ["wx", "exclusive", "atomic", "flag", "race", "toctou"]},
    {"id": "rw_20", "category": "Context Loss",
     "code": "class DataPoller {\n  constructor(interval) {\n    this.data = [];\n    this.interval = interval;\n  }\n  start() {\n    setTimeout(function() {\n      this.data.push(Date.now());\n      setTimeout(arguments.callee, this.interval);\n    }, this.interval);\n  }\n}",
     "pass_keywords": ["arrow", "bind", "this", "=>", ".bind(this)"]}
]

def score_response(keywords, response):
    if not response:
        return "fail"
    r = response.lower()
    matched = [kw for kw in keywords if kw.lower() in r]
    has_code = any(tok in r for tok in ["function", "const ", "async", "=>", "return", "await"])
    if len(matched) >= 2 and has_code:
        return "pass"
    elif len(matched) >= 1 or has_code:
        return "partial"
    return "fail"

def call_base_model_api(code, prompt):
    # Sử dụng Qwen2.5-Coder-1.5B-Instruct làm base model (hoặc bản base nếu không chat)
    API_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-Coder-1.5B-Instruct"
    
    if not HF_TOKEN:
        print("Lỗi: Cần HF_TOKEN để gọi API.")
        return ""
        
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 512,
            "temperature": 0.2,
            "do_sample": False,
            "return_full_text": False,
        },
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {HF_TOKEN}"
    }
    
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(API_URL, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
            if isinstance(result, list) and result:
                raw_output = result[0].get("generated_text", "")
            elif isinstance(result, dict) and "error" in result:
                print(f"Model loading, estimated time: {result.get('estimated_time', 'unknown')}s. Vui lòng thử lại sau.")
                return ""
            else:
                raw_output = str(result)
            return raw_output
    except Exception as e:
        print(f"API Error: {e}")
        return ""

def main():
    print("Khởi tạo RAG Pipeline (BM25 Retriever)...")
    kb_path = os.path.join(os.path.dirname(__file__), "..", "..", "knowledge-base", "knowledge_base_extended.json")
    retriever = load_retriever(kb_path)
    
    # Ghi đè hàm get_llm_fix để gọi Base Model thay vì Mock hay HF Space
    original_get_llm_fix = llm_client.get_llm_fix
    
    def override_get_llm_fix(code, prompt):
        return call_base_model_api(code, prompt)
        
    llm_client.get_llm_fix = override_get_llm_fix
    
    MODEL_LABEL = "Qwen/Qwen2.5-Coder-1.5B-Instruct (Base Model) + RAG Pipeline"
    print("=" * 70)
    print(f"ThreadLearn — RAG Benchmark")
    print(f"Model: {MODEL_LABEL}")
    print("=" * 70)
    
    results = []
    pass_count = partial_count = fail_count = 0
    
    for tc in REAL_WORLD_CASES:
        print(f"\n[{tc['id']}] {tc['category']}")
        t0 = time.time()
        
        # Chạy toàn bộ pipeline (AST -> BM25 -> Prompt -> LLM)
        issues, docs_used = rag_pipeline.run(tc["code"], "javascript", retriever)
        
        # Lấy code LLM sinh ra (rag_pipeline tự động bọc code trả về trong issues[0].fix)
        response_text = issues[0].fix if issues else ""
        
        latency = time.time() - t0
        verdict = score_response(tc["pass_keywords"], response_text)
        
        if verdict == "pass":
            pass_count += 1
            icon = "✅ PASS   "
        elif verdict == "partial":
            partial_count += 1
            icon = "⚠️  PARTIAL"
        else:
            fail_count += 1
            icon = "❌ FAIL   "
            
        print(f"  {icon} | {latency:.1f}s")
        print(f"  {response_text[:100].replace(chr(10), ' ')}...")
        
        results.append({
            "id": tc["id"],
            "category": tc["category"],
            "verdict": verdict,
            "latency_s": round(latency, 2),
            "response_preview": response_text[:200]
        })
        
    score = pass_count + partial_count * 0.5
    print("\n" + "=" * 70)
    print(f"RESULTS — {MODEL_LABEL}")
    print(f"  Pass:    {pass_count}/20")
    print(f"  Partial: {partial_count}/20")
    print(f"  Fail:    {fail_count}/20")
    print(f"  Score:   {score:.1f}/20  ({pass_count/20*100:.0f}% full pass)")
    print("=" * 70)

if __name__ == "__main__":
    main()
