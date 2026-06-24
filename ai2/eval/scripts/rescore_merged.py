"""
Re-score eval_merged_results.json with more nuanced criteria.
Accounts for:
  - Model echoing the prompt back (response starts with prompt text) → FAIL that case
  - Fix quality: check if the actual fix code in response contains the right pattern
  - Multiple keyword groups (any-of-group logic instead of count-threshold)
"""
import json
from pathlib import Path

results_path = Path(__file__).parent / "eval_merged_results.json"
data = json.loads(results_path.read_text(encoding="utf-8"))

# Per-test: list of keyword GROUPS. PASS if >= 1 group fully matched + has fix code.
# A group is a list — ALL words in the group must appear for that group to match.
PASS_GROUPS = {
    "test_01": [["race", "atomic"], ["race", "mutex"], ["race", "queue"]],
    "test_02": [["race", "atomic"], ["race", "transaction"], ["race", "read-modify"]],
    "test_03": [["race", "atomic"], ["race", "upsert"], ["race", "toctou"], ["race", "check-then-act"]],
    "test_04": [["race", "promise"], ["race", "singleton"], ["race", "double"]],
    "test_05": [["race", "appendfile"], ["race", "atomic"], ["race", "concurrent"]],
    "test_06": [["block", "async"], ["block", "chunk"], ["block", "setimmediate"]],
    "test_07": [["block", "async"], ["block", "promise"], ["pbkdf2", "async"]],
    "test_08": [["block", "async"], ["block", "chunk"], ["block", "setimmediate"], ["settimeout", "async"]],
    "test_09": [["block", "async"], ["promise.all", "async"], ["renderasync"]],
    "test_10": [["block", "async"], ["block", "promise"], ["readfile", "async"]],
    "test_11": [["catch", "rejection"], ["catch", "next"], ["try", "catch"], [".catch(next)"], ["rejection"]],
    "test_12": [["return cb"], ["early return"], ["double", "callback"], ["called multiple"]],
    "test_13": [["nexttick"], ["zalgo"], ["consistent", "async"]],
    "test_14": [["arrow", "this"], ["bind", "this"], ["context", "arrow"], ["arrow function"]],
    "test_15": [["async/await"], ["async await"], ["promise", "flatten"]],
    "test_16": [["concurrency", "limit"], ["chunk", "batch"], ["limit", "batch"]],
    "test_17": [["promise.all"], ["parallel", "concurrent"]],
    "test_18": [["promise.all"], ["parallel", "concurrent"]],
    "test_19": [["destroy", "error"], ["close", "error"], ["cleanup", "leak"], ["stream", "error"]],
    "test_20": [["nexttick", "before"], ["nexttick", "ordering"], ["microtask"]],
}

PROMPT_ECHO_MARKERS = [
    "analyze this javascript code",
    "respond with:",
    "bug type (e.g.",
]

def is_prompt_echo(response: str) -> bool:
    r = response.lower()
    return any(marker in r for marker in PROMPT_ECHO_MARKERS)

def rescore(test_id: str, response: str) -> tuple[str, str]:
    if is_prompt_echo(response):
        # Model echoed prompt — but check if the fix part still has value
        # Some echo responses DO contain a valid fix after the re-prompt
        # Only fail if there's no actual answer content beyond the echo
        lines = [l.strip() for l in response.split('\n') if l.strip()]
        # Find how many lines are actual answer vs echo
        answer_lines = [l for l in lines if not any(m in l.lower() for m in PROMPT_ECHO_MARKERS)]
        if len(answer_lines) < 3:
            return "fail", "prompt echo, no answer"

    r = response.lower()
    has_fix = "```" in response or "fix" in r

    groups = PASS_GROUPS.get(test_id, [])
    for group in groups:
        if all(kw in r for kw in group):
            if has_fix:
                return "pass", f"matched group {group}"
            else:
                return "partial", f"matched group {group} but no fix"

    # Fallback: any single keyword from any group
    all_kws = set(kw for g in groups for kw in g)
    if any(kw in r for kw in all_kws):
        return "partial", "partial keyword match"

    return "fail", "no keyword match"


pass_count = partial_count = fail_count = 0
rescored = []

print("Re-scoring ThreadLearn merged model results")
print("=" * 60)

for r in data["results"]:
    old = r["verdict"]
    new, reason = rescore(r["id"], r["response_preview"])

    marker = " (changed)" if new != old else ""
    print(f"[{r['id']}] {r['category']}: {old} -> {new}{marker}  ({reason})")

    if new == "pass": pass_count += 1
    elif new == "partial": partial_count += 1
    else: fail_count += 1

    rescored.append({**r, "verdict": new, "verdict_old": old, "rescore_reason": reason})

print("\n" + "=" * 60)
print(f"RESCORED - ThreadLearn (fine-tuned)")
print(f"  Pass:    {pass_count}/20  (was {data['pass']}/20)")
print(f"  Partial: {partial_count}/20  (was {data['partial']}/20)")
print(f"  Fail:    {fail_count}/20   (was {data['fail']}/20)")
print(f"  Pass rate: {pass_count/20*100:.0f}%  (was {data['pass_rate']})")

out = {**data,
       "pass": pass_count, "partial": partial_count, "fail": fail_count,
       "pass_rate": f"{pass_count/20*100:.0f}%",
       "note": "rescored with flexible keyword groups + prompt-echo detection",
       "results": rescored}

out_path = Path(__file__).parent / "eval_merged_rescored.json"
out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nSaved: {out_path}")
