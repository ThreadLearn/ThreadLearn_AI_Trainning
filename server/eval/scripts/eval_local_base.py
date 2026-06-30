"""
Baseline evaluation: Qwen2.5-Coder-1.5B-Instruct (no fine-tune) — local inference
Runs 20 test cases, scores pass/partial/fail, outputs JSON results.
Model path: ../models/base/
"""
import os, json, time, sys
from pathlib import Path

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
except ImportError:
    print("Run: pip install transformers torch accelerate")
    sys.exit(1)

MODEL_PATH = str(Path(__file__).parent.parent / "models" / "base")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device: {DEVICE}")
if DEVICE == "cuda":
    print(f"GPU: {torch.cuda.get_device_name(0)}")

TEST_CASES = [
    {"id": "test_01", "category": "Race Condition",
     "code": "let counter = 0;\nfunction increment() {\n  setTimeout(() => {\n    counter++;\n  }, Math.random() * 100);\n}\nincrement(); increment();"},
    {"id": "test_02", "category": "Race Condition",
     "code": "const updateAccount = async (id, amount) => {\n  const balance = await db.getBalance(id);\n  setTimeout(() => db.setBalance(id, balance + amount), 10);\n};"},
    {"id": "test_03", "category": "Race Condition",
     "code": "const checkAndCreateUser = (email) => {\n  db.find({email}).then(user => {\n    if (!user) db.create({email});\n  });\n};"},
    {"id": "test_04", "category": "Race Condition",
     "code": "let cache = null;\nfunction getCache() {\n  if (!cache) {\n    fetchData().then(d => cache = d);\n  }\n  return cache;\n}"},
    {"id": "test_05", "category": "Race Condition",
     "code": "let logs = '';\nfunction appendLog(msg) {\n  fs.readFile('log.txt', 'utf8', (err, data) => {\n    fs.writeFile('log.txt', data + msg, () => {});\n  });\n}"},
    {"id": "test_06", "category": "Event Loop Blocking",
     "code": "function processHugeArray(arr) {\n  for(let i=0; i < arr.length; i++) {\n    heavyMath(arr[i]);\n  }\n}"},
    {"id": "test_07", "category": "Event Loop Blocking",
     "code": "const crypto = require('crypto');\nfunction encryptPasswords(users) {\n  users.forEach(u => {\n    u.hash = crypto.pbkdf2Sync(u.password, 'salt', 100000, 64, 'sha512');\n  });\n}"},
    {"id": "test_08", "category": "Event Loop Blocking",
     "code": "const parseJSONLines = (lines) => {\n  lines.forEach(line => {\n    JSON.parse(line);\n  });\n};"},
    {"id": "test_09", "category": "Event Loop Blocking",
     "code": "function renderPages(pages) {\n  return pages.map(page => renderSync(page));\n}"},
    {"id": "test_10", "category": "Event Loop Blocking",
     "code": "const fs = require('fs');\nfunction backupLogs(files) {\n  files.forEach(f => {\n    const data = fs.readFileSync(f);\n    fs.writeFileSync(f + '.bak', data);\n  });\n}"},
    {"id": "test_11", "category": "Unhandled Rejection",
     "code": "app.get('/', (req, res) => {\n  db.query().then(data => res.json(data));\n});"},
    {"id": "test_12", "category": "Double Callback",
     "code": "function getUser(id, cb) {\n  db.findById(id, (err, user) => {\n    if (err) cb(err);\n    if (!user) cb(new Error('Not found'));\n    cb(null, user);\n  });\n}"},
    {"id": "test_13", "category": "Zalgo",
     "code": "const cache = {};\nfunction fetchObj(id, cb) {\n  if (cache[id]) return cb(cache[id]);\n  networkFetch(id, (data) => {\n    cache[id] = data; cb(data);\n  });\n}"},
    {"id": "test_14", "category": "Context Loss",
     "code": "class Service {\n  constructor() { this.name = 'Serv'; }\n  run() {\n    setTimeout(function() {\n      console.log(this.name + ' running');\n    }, 100);\n  }\n}"},
    {"id": "test_15", "category": "Callback Hell",
     "code": "function doTask(cb) {\n  step1(r1 => {\n    step2(r1, r2 => {\n      step3(r2, r3 => {\n        cb(r3);\n      });\n    });\n  });\n}"},
    {"id": "test_16", "category": "Resource Exhaustion",
     "code": "async function downloadAll(urls) {\n  return await Promise.all(urls.map(url => fetch(url)));\n}"},
    {"id": "test_17", "category": "Sequential Awaits",
     "code": "async function getDashboard(id) {\n  const user = await db.getUser(id);\n  const stats = await db.getStats(id);\n  const friends = await db.getFriends(id);\n  return {user, stats, friends};\n}"},
    {"id": "test_18", "category": "Missing Promise.all",
     "code": "async function sendEmails(users) {\n  for(let i=0; i<users.length; i++) {\n    await emailService.send(users[i].email);\n  }\n}"},
    {"id": "test_19", "category": "Buffer Leak",
     "code": "function streamData(req, res) {\n  const rs = fs.createReadStream('file.mp4');\n  rs.pipe(res);\n}"},
    {"id": "test_20", "category": "Event Loop Ordering",
     "code": "let init = false;\nprocess.nextTick(() => init = true);\nsetTimeout(() => console.log(init), 0);"},
]

PASS_KEYWORDS = {
    "test_01": ["atomic", "mutex", "queue", "race"],
    "test_02": ["transaction", "atomic", "race", "read-modify"],
    "test_03": ["toctou", "upsert", "race", "check-then-act", "atomic"],
    "test_04": ["double", "init", "promise", "singleton"],
    "test_05": ["appendfile", "atomic", "race", "concurrent"],
    "test_06": ["setimmediate", "chunk", "async", "block"],
    "test_07": ["pbkdf2", "async", "promise", "block"],
    "test_08": ["setimmediate", "async", "chunk", "block"],
    "test_09": ["async", "promise.all", "renderasync", "block"],
    "test_10": ["readfile", "promise", "async", "block"],
    "test_11": ["catch", "next(err)", "try", "rejection"],
    "test_12": ["return cb", "early return", "double", "called multiple"],
    "test_13": ["nexttick", "async", "zalgo", "consistent"],
    "test_14": ["arrow", "bind", "this", "context"],
    "test_15": ["async/await", "async await", "flatten", "promise"],
    "test_16": ["concurrency", "chunk", "limit", "batch"],
    "test_17": ["promise.all", "parallel", "concurrent"],
    "test_18": ["promise.all", "parallel", "concurrent"],
    "test_19": ["destroy", "close", "error", "cleanup", "leak"],
    "test_20": ["nexttick", "microtask", "ordering", "before"],
}

SYSTEM_PROMPT = "You are an expert JavaScript concurrency bug detector. Analyze code for race conditions, event loop blocking, callback issues, and async bugs. Be specific and concise."

USER_PROMPT = """Analyze this JavaScript code for concurrency bugs:

```javascript
{code}
```

Respond with:
1. Bug type (e.g. Race Condition, Event Loop Blocking, etc.)
2. Brief explanation (1-2 sentences)
3. Fixed code snippet"""


def score(test_id, response):
    resp_lower = response.lower()
    keywords = PASS_KEYWORDS.get(test_id, [])
    matched = [kw for kw in keywords if kw in resp_lower]
    has_fix = "```" in response or "fix" in resp_lower
    if len(matched) >= 2 and has_fix:
        return "pass"
    elif len(matched) >= 1:
        return "partial"
    return "fail"


def main():
    print(f"\nLoading model from {MODEL_PATH} ...")
    t0 = time.time()

    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()
    print(f"Model loaded in {time.time()-t0:.1f}s\n")

    print("Evaluating Qwen2.5-Coder-1.5B-Instruct (no fine-tune)")
    print("=" * 60)

    results = []
    pass_count = partial_count = fail_count = 0

    for tc in TEST_CASES:
        print(f"\n[{tc['id']}] {tc['category']}")
        try:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT.format(code=tc["code"])},
            ]
            text = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = tokenizer([text], return_tensors="pt").to(DEVICE)

            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=512,
                    temperature=0.01,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id,
                )
            generated = outputs[0][inputs["input_ids"].shape[1]:]
            response = tokenizer.decode(generated, skip_special_tokens=True)
        except Exception as e:
            print(f"  ERROR: {e}")
            response = ""

        verdict = score(tc["id"], response)
        if verdict == "pass":
            pass_count += 1
        elif verdict == "partial":
            partial_count += 1
        else:
            fail_count += 1

        print(f"  [{verdict.upper()}] {response.strip()[:100].replace(chr(10), ' ')}...")
        results.append({
            "id": tc["id"],
            "category": tc["category"],
            "verdict": verdict,
            "response_preview": response.strip()[:300],
        })

    print("\n" + "=" * 60)
    print(f"RESULTS - Qwen2.5-Coder-1.5B (no fine-tune)")
    print(f"  Pass:    {pass_count}/20")
    print(f"  Partial: {partial_count}/20")
    print(f"  Fail:    {fail_count}/20")
    print(f"  Pass rate: {pass_count/20*100:.0f}%")

    output = {
        "model": "Qwen2.5-Coder-1.5B-Instruct (no fine-tune)",
        "total": 20,
        "pass": pass_count,
        "partial": partial_count,
        "fail": fail_count,
        "pass_rate": f"{pass_count/20*100:.0f}%",
        "results": results,
    }
    out_path = Path(__file__).parent / "eval_base_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
