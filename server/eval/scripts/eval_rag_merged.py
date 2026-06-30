"""
Evaluation: ThreadLearn fine-tuned model with correct RAG pipeline format.

Training prompt format (from ai1_02_format_jsonl.py):
    "Convert to concurrent JavaScript:\n\n{code}\n"

RAG pipeline augments with BM25 context docs (from rag_pipeline.py _build_prompt).
This eval tests both:
  - raw model format (as trained)
  - RAG-augmented format (as used in production)

Scoring: semantic — checks if output contains correct fix pattern for each bug.
"""
import os, sys, json, time
from pathlib import Path

# Add server dir to path for BM25 imports
UNIT_DIR = Path(__file__).parent.parent.parent  # server/eval/scripts -> server/
ROOT_DIR = UNIT_DIR.parent                       # server/ -> repo root
SERVER_DIR = UNIT_DIR / "server"
sys.path.insert(0, str(SERVER_DIR))
KB_PATH = str(UNIT_DIR / "knowledge-base" / "knowledge_base.json")

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
except ImportError:
    print("Run: pip install transformers torch")
    sys.exit(1)

MODEL_PATH = str(ROOT_DIR / "models" / "merged")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device: {DEVICE} | {torch.cuda.get_device_name(0) if DEVICE == 'cuda' else 'CPU'}")

# ---------------------------------------------------------------------------
# Load BM25 retriever
# ---------------------------------------------------------------------------
try:
    from bm25_module import load_retriever
    retriever = load_retriever(KB_PATH)
    print(f"BM25 loaded: {retriever.doc_count} docs")
    USE_RAG = True
except Exception as e:
    print(f"BM25 load failed: {e} — running without RAG")
    retriever = None
    USE_RAG = False

# ---------------------------------------------------------------------------
# Test cases (same 20 as before)
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Expected fix patterns — what the OUTPUT CODE should contain (not label)
# Focus on the FIX, not the bug name label
# ---------------------------------------------------------------------------
FIX_PATTERNS = {
    "test_01": [["mutex", "queue"], ["async", "await"], ["counter"]],
    "test_02": [["transaction"], ["async", "await", "setbalance"], ["await db"]],
    "test_03": [["upsert"], ["atomic"], ["findoneandupdate"], ["createifnotexists"]],
    "test_04": [["cachepromise", "null"], ["if.*promise", "return"], ["singleton"]],
    "test_05": [["appendfile"], ["atomic"], ["fs.promises"]],
    "test_06": [["setimmediate"], ["chunk"], ["yield"], ["async"]],
    "test_07": [["pbkdf2("], ["pbkdf2.then"], ["async", "pbkdf2"]],
    "test_08": [["setimmediate"], ["async", "json.parse"], ["yield"]],
    "test_09": [["renderasync"], ["promise.all"], ["async"]],
    "test_10": [["fs.promises"], ["readfile("], ["async", "await"]],
    "test_11": [[".catch"], ["catch(next"], ["catch(err"], ["try {"]],
    "test_12": [["return cb(err"], ["return cb(new"], ["if (err) return"]],
    "test_13": [["nexttick"], ["process.nexttick"], ["settimeout.*0"]],
    "test_14": [["=>"], ["arrow"], [".bind(this"]],
    "test_15": [["async", "await", "step"], ["promise.then"]],
    "test_16": [["chunk"], ["limit"], ["slice"], ["batch"]],
    "test_17": [["promise.all("], ["await promise.all"]],
    "test_18": [["promise.all("], ["await promise.all"]],
    "test_19": [[".on('error'"], ["rs.destroy"], [".on(\"error\""]],
    "test_20": [["settimeout", "nexttick"], ["init", "true"]],
}


def score(test_id: str, response: str) -> tuple[str, str]:
    """
    Score based on fix code content, not bug label.
    PASS: response contains correct fix pattern
    PARTIAL: response is non-empty, has code, but fix pattern not matched
    FAIL: empty, echo, or completely wrong
    """
    r = response.lower().replace("\n", " ")

    # Detect prompt echo (model repeated prompt instead of answering)
    if r.strip().startswith("convert to concurrent javascript"):
        # Still might have answer after echo — check length
        if len(r) < 200:
            return "fail", "prompt echo only"

    has_code = "function" in r or "const " in r or "async" in r or "=>" in r or "return" in r

    patterns = FIX_PATTERNS.get(test_id, [])
    for group in patterns:
        if all(kw in r for kw in group):
            return "pass", f"fix pattern matched: {group}"

    if has_code:
        return "partial", "has code but fix pattern not matched"
    return "fail", "no code in response"


def build_rag_prompt(code: str) -> str:
    """Build prompt with BM25 context — mirrors rag_pipeline._build_prompt()"""
    from bm25_module import tokenize
    query_tokens = tokenize(code)
    query = " ".join(query_tokens[:20])
    docs = retriever.search(query, top_k=3) if query else []

    context_parts = []
    for i, doc in enumerate(docs, 1):
        context_parts.append(
            f"Tai lieu {i} - {doc.get('title', '')} [{doc.get('category', '')}]:\n"
            f"{doc.get('content', '')}"
        )
    context = "\n\n".join(context_parts)

    if context:
        return (
            f"Duoi day la cac tai lieu tham khao ve concurrent JavaScript:\n\n"
            f"{context}\n\n"
            f"---\n\n"
            f"Convert to concurrent JavaScript:\n\n{code}\n"
        )
    else:
        return f"Convert to concurrent JavaScript:\n\n{code}\n"


def build_raw_prompt(code: str) -> str:
    """Exact training format from ai1_02_format_jsonl.py"""
    return f"Convert to concurrent JavaScript:\n\n{code}\n"


def run_inference(model, tokenizer, prompt: str) -> str:
    inputs = tokenizer([prompt], return_tensors="pt").to(DEVICE)
    input_len = inputs["input_ids"].shape[1]

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=300,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
            repetition_penalty=1.1,
        )
    generated = outputs[0][input_len:]
    return tokenizer.decode(generated, skip_special_tokens=True).strip()


def main():
    print(f"\nLoading ThreadLearn fine-tuned model...")
    t0 = time.time()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()
    print(f"Model loaded in {time.time()-t0:.1f}s\n")

    results_raw = []
    results_rag = []
    pass_raw = partial_raw = fail_raw = 0
    pass_rag = partial_rag = fail_rag = 0

    print("=" * 70)
    print(f"{'ID':<10} {'Category':<22} {'RAW':>6} {'RAG':>6}")
    print("=" * 70)

    for tc in TEST_CASES:
        # --- RAW (training format) ---
        prompt_raw = build_raw_prompt(tc["code"])
        resp_raw = run_inference(model, tokenizer, prompt_raw)
        v_raw, reason_raw = score(tc["id"], resp_raw)

        if v_raw == "pass": pass_raw += 1
        elif v_raw == "partial": partial_raw += 1
        else: fail_raw += 1

        # --- RAG augmented ---
        if USE_RAG:
            prompt_rag = build_rag_prompt(tc["code"])
            resp_rag = run_inference(model, tokenizer, prompt_rag)
            v_rag, reason_rag = score(tc["id"], resp_rag)
        else:
            resp_rag = resp_raw
            v_rag, reason_rag = v_raw, reason_raw

        if v_rag == "pass": pass_rag += 1
        elif v_rag == "partial": partial_rag += 1
        else: fail_rag += 1

        print(f"[{tc['id']}] {tc['category']:<22} {v_raw.upper():>8} {v_rag.upper():>8}")

        results_raw.append({"id": tc["id"], "category": tc["category"],
                             "verdict": v_raw, "reason": reason_raw,
                             "response": resp_raw[:300]})
        results_rag.append({"id": tc["id"], "category": tc["category"],
                             "verdict": v_rag, "reason": reason_rag,
                             "response": resp_rag[:300]})

    print("=" * 70)
    print(f"\nRESULTS — ThreadLearn fine-tuned (correct prompt format)")
    print(f"  RAW (training format):  Pass {pass_raw}/20 ({pass_raw*5}%)  "
          f"Partial {partial_raw}/20  Fail {fail_raw}/20")
    print(f"  RAG (+ BM25 context):   Pass {pass_rag}/20 ({pass_rag*5}%)  "
          f"Partial {partial_rag}/20  Fail {fail_rag}/20")

    output = {
        "model": "ThreadLearn (Qwen2.5-Coder-1.5B fine-tuned)",
        "prompt_format": "Convert to concurrent JavaScript (training format)",
        "rag_enabled": USE_RAG,
        "raw": {"pass": pass_raw, "partial": partial_raw, "fail": fail_raw,
                "pass_rate": f"{pass_raw*5}%", "results": results_raw},
        "rag": {"pass": pass_rag, "partial": partial_rag, "fail": fail_rag,
                "pass_rate": f"{pass_rag*5}%", "results": results_rag},
    }
    out_path = UNIT_DIR / "eval" / "results" / "eval_rag_results.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
