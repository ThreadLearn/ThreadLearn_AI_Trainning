import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
import os
import re
import time
import argparse
import requests
from dotenv import load_dotenv

# Try to load BM25, install rank_bm25 if needed
try:
    from rank_bm25 import BM25Okapi
except ImportError:
    print("rank_bm25 not found. Install it first: pip install rank-bm25")
    exit(1)

# Load ENV
env_path = os.path.join(os.path.dirname(__file__), "..", "..", "server", ".env")
load_dotenv(env_path)
HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    print("WARNING: HF_TOKEN not set in ai2/server/.env")

MODEL_ID = "anha12/threadlearn-qwen2.5-coder-1.5b-cot-v2"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"

def get_real_world_cases():
    notebook_path = os.path.join(os.path.dirname(__file__), "notebooks", "with_pipeline", "kaggle_pipeline_merged.ipynb")
    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            source = "".join(cell["source"])
            if "REAL_WORLD_CASES = [" in source:
                # Extract the JSON array
                start = source.find("REAL_WORLD_CASES = [") + len("REAL_WORLD_CASES = ")
                end = source.rfind("]") + 1
                cases_json = source[start:end]
                return json.loads(cases_json)
    return []

REAL_WORLD_CASES = get_real_world_cases()

def score_response(keywords, response):
    if not response: return "fail"
    r = response.lower()
    matched = [kw for kw in keywords if kw.lower() in r]
    has_code = any(tok in r for tok in ["function", "const ", "async", "=>", "return", "await"])
    if len(matched) >= 2 and has_code: return "pass"
    elif len(matched) >= 1 or has_code: return "partial"
    return "fail"

def call_hf_api(prompt, attempt=1, max_retries=5):
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 2048,
            "temperature": 0.2,
            "do_sample": False,
            "return_full_text": False,
        },
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {HF_TOKEN}",
    }
    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=180)
        if response.status_code == 503:
            try:
                wait = response.json().get("estimated_time", 20)
                print(f"  [HTTP 503] Model loading. Waiting {wait}s (attempt {attempt}/{max_retries})...")
                time.sleep(wait)
                if attempt < max_retries:
                    return call_hf_api(prompt, attempt + 1, max_retries)
            except Exception:
                pass
        
        response.raise_for_status()
        result = response.json()
        
        if isinstance(result, list) and result:
            return result[0].get("generated_text", "")
        elif isinstance(result, dict):
            if "error" in result:
                wait = result.get("estimated_time", 20)
                print(f"  [Wait] Model loading. Waiting {wait}s...")
                time.sleep(wait)
                if attempt < max_retries:
                    return call_hf_api(prompt, attempt + 1, max_retries)
            return result.get("generated_text", "")
        return str(result)
    except requests.exceptions.HTTPError as e:
        print(f"  [HTTPError] {e}")
        if attempt < max_retries:
            time.sleep(5)
            return call_hf_api(prompt, attempt + 1, max_retries)
    except Exception as e:
        print(f"  [Error] {e}")
        if attempt < max_retries:
            time.sleep(5)
            return call_hf_api(prompt, attempt + 1, max_retries)
    return ""

STOPWORDS = {
    "the","a","an","is","in","on","at","to","for","of","and","or","with",
    "this","that","it","be","are","was","were","has","have","had","do","does",
    "did","not","by","from","as","if","when","then","so","but","also","can",
    "will","use","used","using","should","would","could","may","each","how",
    "what","which","who","into","after","before","its","their","they","we",
    "you","he","she","i","me",
}

def _split_camel(token):
    p = re.sub(r"([a-z])([A-Z])", r"\1 \2", token)
    p = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", p)
    return p.lower().split()

def bm25_tokenize(text):
    tokens = []
    for raw in re.split(r"[^a-zA-Z0-9]+", text):
        if not raw: continue
        for sub in _split_camel(raw):
            if len(sub) >= 2 and sub not in STOPWORDS:
                tokens.append(sub)
    return tokens

def build_bm25_index(docs):
    corpus = [bm25_tokenize(f"{d.get('title','')} {d.get('content','')}") for d in docs]
    return BM25Okapi(corpus), docs

def bm25_search(index, docs, query, top_k=3):
    q_tokens = bm25_tokenize(query)
    if not q_tokens: return []
    scores = index.get_scores(q_tokens)
    top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k*5]
    results, seen = [], set()
    for idx in top_idx:
        if scores[idx] > 0:
            doc = docs[idx]
            base = re.sub(r'\s*\[.*?\]\s*$', '', doc.get('title','')).strip()
            if base not in seen:
                seen.add(base)
                d = dict(doc); d["bm25_score"] = round(float(scores[idx]), 3)
                results.append(d)
                if len(results) >= top_k: break
    return results

JS_KEYWORDS = {
    "var","let","const","function","return","if","else","for","while","do",
    "try","catch","throw","new","class","extends","import","export","from",
    "async","await","then","null","undefined","true","false","typeof","instanceof",
}

def extract_keywords(code):
    clean = re.sub(r"'[^']*'|\"[^\"]*\"", " ", code)
    clean = re.sub(r"//.*", " ", clean)
    tokens = re.findall(r"[a-zA-Z_$][a-zA-Z0-9_$]*", clean)
    kw = [t for t in tokens if t.lower() not in JS_KEYWORDS and len(t) >= 3]
    seen, result = set(), []
    for k in kw:
        if k not in seen: seen.add(k); result.append(k)
    return " ".join(result[:20])

def build_prompt(code, docs=None):
    if docs:
        parts = [
            f"Reference {i} — {d.get('title','')} [{d.get('category','')}]:\n{d.get('content','')[:500]}"
            for i, d in enumerate(docs, 1)
        ]
        ctx = "\n\n".join(parts)
        return f"JavaScript concurrency reference docs:\n\n{ctx}\n\n---\n\nConvert to concurrent JavaScript:\n\n{code}\n"
    return f"Convert to concurrent JavaScript:\n\n{code}\n"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pipeline", action="store_true")
    args = parser.parse_args()

    TOTAL = len(REAL_WORLD_CASES)
    if TOTAL == 0:
        print("Failed to load REAL_WORLD_CASES")
        return
    print(f"Loaded {TOTAL} real-world cases.")

    bm25_index = None
    bm25_docs = None
    if args.pipeline:
        kb_path = os.path.join(os.path.dirname(__file__), "..", "..", "knowledge-base", "knowledge_base.json")
        with open(kb_path, encoding="utf-8") as f:
            kb_docs = json.load(f)
        bm25_index, bm25_docs = build_bm25_index(kb_docs)
        print(f"BM25 pipeline ready — {len(kb_docs)} docs indexed")
        out_file = os.path.join(os.path.dirname(__file__), "results", "with_pipeline", "eval_cot_v2_pipeline_results.json")
    else:
        out_file = os.path.join(os.path.dirname(__file__), "results", "without_pipeline", "eval_cot_v2_results.json")

    results = []
    pass_count = partial_count = fail_count = 0

    print("=" * 70)
    print(f"ThreadLearn — Real-World Benchmark: {MODEL_ID}")
    print(f"Pipeline: {args.pipeline}")
    print("=" * 70)

    for tc in REAL_WORLD_CASES:
        print(f"\n[{tc['id']}] {tc['category']}")
        t0 = time.time()
        
        if args.pipeline:
            query = extract_keywords(tc["code"])
            docs = bm25_search(bm25_index, bm25_docs, query, top_k=3)
            prompt = build_prompt(tc["code"], docs)
        else:
            prompt = build_prompt(tc["code"])

        response = call_hf_api(prompt)
        latency = time.time() - t0
        
        verdict = score_response(tc["pass_keywords"], response)
        if verdict == "pass":      pass_count += 1;    icon = "✅ PASS   "
        elif verdict == "partial": partial_count += 1; icon = "⚠️  PARTIAL"
        else:                      fail_count += 1;    icon = "❌ FAIL   "
        
        print(f"  {icon} | {latency:.1f}s")
        if args.pipeline:
            print(f"  Docs: {[(d.get('title','')[:40], d.get('bm25_score')) for d in docs]}")
        
        res_dict = {
            "id": tc["id"], 
            "category": tc["category"],
            "verdict": verdict, 
            "latency_s": round(latency, 2),
            "response_preview": response[:400]
        }
        if args.pipeline:
            res_dict["bm25_query"] = query
            res_dict["docs_retrieved"] = [(d.get("title",""), d.get("bm25_score")) for d in docs]
        results.append(res_dict)

    score = pass_count + partial_count * 0.5
    print("\n" + "=" * 70)
    print(f"RESULTS — {MODEL_ID}")
    print(f"  Pass:    {pass_count}/{TOTAL}")
    print(f"  Partial: {partial_count}/{TOTAL}")
    print(f"  Fail:    {fail_count}/{TOTAL}")
    print(f"  Score:   {score:.1f}/{TOTAL}  ({pass_count/TOTAL*100:.0f}% full pass)")
    print("=" * 70)

    output = {
        "model": MODEL_ID, 
        "pipeline": "BM25+AST" if args.pipeline else "none",
        "pass": pass_count, 
        "partial": partial_count, 
        "fail": fail_count,
        "score": f"{score:.1f}/{TOTAL}", 
        "results": results
    }
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"\n💾 Saved: {out_file}")

if __name__ == "__main__":
    main()
