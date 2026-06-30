"""
Read-only dataset audit for ThreadLearn AI1.
Applies the mle-workflow Data Contract checks: schema, empties, duplicates,
train/eval leakage, length distribution, prompt-format consistency.
Does NOT modify any dataset file.
"""
import json, hashlib, os, collections

BASE = os.path.join(os.path.dirname(__file__), "processed")

FILES = [
    "threadlearn_train.jsonl",
    "threadlearn_train_master.jsonl",
    "threadlearn_train_eval.jsonl",
    "threadlearn_train_cot_master.jsonl",
    "threadlearn_patch_5cases.jsonl",
    "threadlearn_patch_augmented.jsonl",
    "threadlearn_patch_cot.jsonl",
]

def load(path):
    rows, errs = [], []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception as e:
                errs.append((i, str(e)[:60]))
    return rows, errs

def norm(s):
    return (s or "").strip()

def keyfn(r):
    # identity of a sample = prompt + completion text
    return hashlib.sha256((norm(r.get("prompt")) + "||" + norm(r.get("completion"))).encode("utf-8")).hexdigest()

def prompt_only_key(r):
    return hashlib.sha256(norm(r.get("prompt")).encode("utf-8")).hexdigest()

report = {}
loaded = {}

print("=" * 70)
print("THREADLEARN DATASET AUDIT  (mle-workflow / Data Contract)")
print("=" * 70)

for fn in FILES:
    path = os.path.join(BASE, fn)
    if not os.path.exists(path):
        print(f"\n[MISSING] {fn}")
        continue
    rows, errs = load(path)
    loaded[fn] = rows
    keys = set()
    empties = 0
    schema_bad = 0
    bad_prefix = 0
    plen, clen = [], []
    prefixes = collections.Counter()
    dup = 0
    for r in rows:
        if not isinstance(r, dict) or "prompt" not in r or "completion" not in r:
            schema_bad += 1
            continue
        p, c = norm(r["prompt"]), norm(r["completion"])
        if not p or not c:
            empties += 1
        plen.append(len(r["prompt"]))
        clen.append(len(r["completion"]))
        # first line of prompt = task instruction
        prefixes[r["prompt"].split("\n", 1)[0][:60]] += 1
        k = keyfn(r)
        if k in keys:
            dup += 1
        keys.add(k)
    def stats(xs):
        if not xs: return "n/a"
        xs2 = sorted(xs)
        return f"min={xs2[0]} p50={xs2[len(xs2)//2]} max={xs2[-1]} avg={sum(xs2)//len(xs2)}"
    report[fn] = {"rows": len(rows), "unique": len(keys), "dup": dup,
                  "empties": empties, "schema_bad": schema_bad,
                  "json_errs": len(errs)}
    print(f"\n--- {fn} ---")
    print(f"  records           : {len(rows)}")
    print(f"  json parse errors : {len(errs)}")
    print(f"  schema bad (no prompt/completion): {schema_bad}")
    print(f"  empty prompt/compl: {empties}")
    print(f"  exact duplicates  : {dup}  (unique={len(keys)})")
    print(f"  prompt len (chars): {stats(plen)}")
    print(f"  compl  len (chars): {stats(clen)}")
    print(f"  task instructions (first line):")
    for pre, n in prefixes.most_common(5):
        print(f"      {n:4d}  {pre!r}")

# ---- Train/Eval leakage check (anti-pattern: split leaks into eval) ----
print("\n" + "=" * 70)
print("LEAKAGE CHECK  (train vs eval overlap)")
print("=" * 70)
pairs = [
    ("threadlearn_train_master.jsonl", "threadlearn_train_eval.jsonl"),
    ("threadlearn_train.jsonl", "threadlearn_train_eval.jsonl"),
    ("threadlearn_train_cot_master.jsonl", "threadlearn_train_eval.jsonl"),
]
for a, b in pairs:
    if a in loaded and b in loaded:
        ka = {keyfn(r) for r in loaded[a] if isinstance(r, dict) and "prompt" in r}
        kb = {keyfn(r) for r in loaded[b] if isinstance(r, dict) and "prompt" in r}
        pa = {prompt_only_key(r) for r in loaded[a] if isinstance(r, dict) and "prompt" in r}
        pb = {prompt_only_key(r) for r in loaded[b] if isinstance(r, dict) and "prompt" in r}
        inter = ka & kb
        pinter = pa & pb
        print(f"\n  {a}  vs  {b}")
        print(f"    |train|={len(ka)}  |eval|={len(kb)}")
        print(f"    exact (prompt+completion) overlap : {len(inter)}  "
              f"({100*len(inter)/max(1,len(kb)):.1f}% of eval)")
        print(f"    prompt-only overlap               : {len(pinter)}  "
              f"({100*len(pinter)/max(1,len(pb)):.1f}% of eval)")
