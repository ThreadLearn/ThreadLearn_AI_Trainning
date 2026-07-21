import os, sys, json, time
from pathlib import Path

# Add server dir to path for BM25 imports
SERVER_DIR = Path(__file__).parent / "server"
sys.path.insert(0, str(SERVER_DIR))
KB_PATH = str(Path(__file__).parent / "knowledge-base" / "knowledge_base.json")

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
except ImportError:
    print("Run: pip install transformers torch")
    sys.exit(1)

# Use the newly patched model from HF directly!
MODEL_PATH = "anha12/threadlearn-qwen2.5-coder-1.5b-merged"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

try:
    from bm25_module import load_retriever
    retriever = load_retriever(KB_PATH)
    USE_RAG = True
except Exception as e:
    retriever = None
    USE_RAG = False

# ==============================================================================
# UNBIASED NEW TEST CASES (Khác hoàn toàn với data training)
# Mục đích: Đảm bảo AI hiểu bản chất (khái quát hóa), không phải học vẹt!
# ==============================================================================
TEST_CASES = [
    {
        "id": "unbiased_01", 
        "category": "Race Singleton Promise",
        "desc": "Object-oriented cache fetch. AI must realize it needs to cache the Promise, not the result data.",
        "code": "class ConfigLoader {\n  constructor() { this.configData = null; }\n  getConfig() {\n    if (!this.configData) {\n      fetch('/api/config').then(res => res.json()).then(data => {\n        this.configData = data;\n      });\n    }\n    return this.configData;\n  }\n}"
    },
    {
        "id": "unbiased_02", 
        "category": "Race File Append",
        "desc": "Logging system using callbacks. AI must replace read+write with atomic appendFile.",
        "code": "function recordAuditTrail(action) {\n  fs.readFile('audit.log', 'utf8', (err, log) => {\n    const entry = log + `[AUDIT]: ${action}\\n`;\n    fs.writeFile('audit.log', entry, (err) => {\n      if(err) console.error(err);\n    });\n  });\n}"
    },
    {
        "id": "unbiased_03", 
        "category": "Double Callback",
        "desc": "Redis cache fetch. AI must use 'return cb' to prevent execution continuing on error.",
        "code": "function fetchCache(key, callback) {\n  redis.get(key, (err, result) => {\n    if (err) callback(err);\n    if (result === null) callback(new Error('Cache miss'));\n    callback(null, JSON.parse(result));\n  });\n}"
    },
    {
        "id": "unbiased_04", 
        "category": "Zalgo",
        "desc": "Global state check vs Async DB call. AI must use process.nextTick for the global state.",
        "code": "function loadAppSettings(cb) {\n  if (global.settingsLoaded) {\n    cb(null, global.settingsData);\n    return;\n  }\n  db.query('SELECT * FROM settings', (err, data) => {\n    global.settingsLoaded = true;\n    global.settingsData = data;\n    cb(null, data);\n  });\n}"
    },
    {
        "id": "unbiased_05", 
        "category": "Buffer Leak",
        "desc": "Proxying audio stream. AI must clean up the upstream request when the client drops.",
        "code": "app.get('/proxy-audio', (req, res) => {\n  const audioStream = http.request('http://internal/audio.wav');\n  audioStream.pipe(res);\n  audioStream.on('error', (e) => res.status(500).end());\n});"
    }
]

# Scoring criteria
FIX_PATTERNS = {
    "unbiased_01": [["this.configpromise"], ["this.promise"], ["this.configdata = fetch"], ["return this."]],
    "unbiased_02": [["appendfile"], ["atomic"], ["fs.promises"]],
    "unbiased_03": [["return callback(err"], ["if (err) return"], ["return callback(new"]],
    "unbiased_04": [["nexttick"], ["process.nexttick"], ["settimeout"]],
    "unbiased_05": [["req.on('close'"], [".destroy("], ["req.on(\"close\""]],
}

def score(test_id: str, response: str) -> tuple[str, str]:
    r = response.lower().replace("\n", " ")
    has_code = "function" in r or "const " in r or "class" in r or "=>" in r or "return" in r
    
    patterns = FIX_PATTERNS.get(test_id, [])
    for group in patterns:
        if all(kw in r for kw in group):
            return "pass", f"Fix pattern matched: {group}"
            
    if has_code:
        return "partial", "Có sinh code nhưng thiếu logic chặn lỗi (không khớp keyword)"
    return "fail", "No code"

def build_rag_prompt(code: str) -> str:
    from bm25_module import tokenize
    query = " ".join(tokenize(code)[:20])
    docs = retriever.search(query, top_k=3) if query else []
    
    context = "\n\n".join(f"Tài liệu {i}:\n{d.get('content', '')}" for i, d in enumerate(docs, 1))
    if context:
        return f"Dưới đây là tài liệu tham khảo:\n\n{context}\n\n---\n\nConvert to concurrent JavaScript:\n\n{code}\n"
    return f"Convert to concurrent JavaScript:\n\n{code}\n"

def run_inference(model, tokenizer, prompt: str) -> str:
    inputs = tokenizer([prompt], return_tensors="pt").to(DEVICE)
    input_len = inputs["input_ids"].shape[1]
    with torch.no_grad():
        outputs = model.generate(
            **inputs, max_new_tokens=300, do_sample=False, 
            pad_token_id=tokenizer.eos_token_id, eos_token_id=tokenizer.eos_token_id
        )
    return tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True).strip()

def main():
    print("=" * 60)
    print("UNBIASED TEST SUITE: Kiểm tra 5 lỗ hổng khó nhất")
    print("=" * 60)
    
    print("\n[1] Đang tải Model từ Hugging Face (sẽ tải bản mới nhất)...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()
    
    print("\n[2] Bắt đầu đánh giá (RAG mode)...\n")
    pass_cnt = 0
    for tc in TEST_CASES:
        prompt = build_rag_prompt(tc["code"]) if USE_RAG else f"Convert to concurrent JavaScript:\n\n{tc['code']}\n"
        resp = run_inference(model, tokenizer, prompt)
        v, reason = score(tc["id"], resp)
        
        if v == "pass": pass_cnt += 1
        
        print(f"🔹 {tc['category']} ({tc['id']})")
        print(f"   => Đánh giá: {v.upper()} | {reason}")
        print("-" * 60)

    print(f"\n[3] TỔNG KẾT UNBIASED TEST: {pass_cnt}/5 PASS")
    if pass_cnt >= 4:
        print("🎉 XUẤT SẮC! Model đã thực sự hiểu bản chất, không bị học vẹt (overfit)!")
    else:
        print("⚠️ Model vẫn bị overfit, chưa khái quát hóa được sang code lạ.")

if __name__ == "__main__":
    main()
