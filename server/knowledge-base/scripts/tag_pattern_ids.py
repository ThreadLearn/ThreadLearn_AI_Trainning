"""
AI2 — gan them field `pattern_ids` (list[str]) vao moi doc trong knowledge_base.json,
khop voi 18 pattern_id cua race_detector.py. KHONG doi/xoa field `category` cu.

Doc khong match rule nao thi `pattern_ids: []` — giu nguyen, khong doan bua.

Chay: python tag_pattern_ids.py
"""
import json
import re
from pathlib import Path

KB_PATH = Path(__file__).parent.parent / "knowledge_base.json"

# Moi pattern_id -> list regex (match tren title+content, case-insensitive).
# Rule bam sat ten bien/API that su xuat hien trong race_detector.py, khong dung
# tu chung chung ("sync", "async", "promise") vi se match gan het KB (da kiem chung).
RULES: dict[str, list[str]] = {
    "closure_loop_var": [r"\bfor\s*\(\s*var\b", r"\bclosure\b.*\bloop\b", r"\bloop\b.*\bclosure\b"],
    "shared_var_settimeout": [r"\bsetTimeout\b", r"\bsetInterval\b"],
    "promise_no_await": [r"\bmissing\s+await\b", r"\bforgot\s+to\s+await\b", r"\bpromise\b.*\bwithout\s+await\b"],
    "concurrent_write_array": [r"\bconcurrent(ly)?\s+writ\w*\s+(to\s+)?array\b", r"\barray\s+mutat\w*\s+concurrent"],
    "counter_no_atomic": [r"\bnon-?atomic\b", r"\brace\b.*\bcounter\b", r"\bcounter\b.*\bincrement\b.*\brace\b"],
    "unhandled_rejection": [r"\bunhandled\s+(promise\s+)?rejection\b", r"\bUnhandledPromiseRejection\b"],
    "double_callback": [r"\bcallback\b.*\bcalled\s+(twice|multiple\s+times)\b", r"\bdouble[- ]?callback\b"],
    "zalgo": [r"\bzalgo\b", r"\breleas\w+\s+zalgo\b", r"\bsync\s+or\s+async\b.*\bcallback\b"],
    "context_loss_this": [r"\bthis\b\s+context\s+lost", r"\blost\s+context\b", r"\barrow\s+function\b.*\bthis\b"],
    "callback_hell": [r"\bcallback\s+hell\b", r"\bpyramid\s+of\s+doom\b"],
    "resource_exhaustion": [r"\bresource\s+exhaustion\b", r"\btoo\s+many\s+(open\s+)?(files|connections|handles)\b", r"\bfile\s+descriptor\s+leak\b"],
    "sequential_awaits": [r"\bsequential\s+await\b", r"\bawait\b.*\bin\s+a?\s*loop\b", r"\bserializ\w+\s+async\s+call"],
    "buffer_leak": [r"\bbuffer\s+leak\b", r"\bmemory\s+leak\b.*\bstream\b", r"\bstream\s+leak\b"],
    "sync_io_blocking": [r"\breadFileSync\b", r"\bwriteFileSync\b", r"\bsync\s+i/o\b", r"\bblock\w*\s+the\s+event\s+loop\b"],
    "global_var_thread": [r"\bglobal\s+variable\b.*\bthread\b", r"\bshared\s+global\s+state\b", r"\bworker_threads\b"],
    "shared_list_no_lock": [r"\bshared\s+(list|array)\b.*\block\b", r"\bwithout\s+(a\s+)?lock\b", r"\bmutex\b"],
    "missing_join": [r"\bmissing\s+join\b", r"\bthread\.join\b", r"\bawait\s+all\b.*\bworker"],
    "singleton_lazy_init": [r"\bsingleton\b", r"\blazy\s+init"],
}

_COMPILED = {pid: [re.compile(p, re.I) for p in pats] for pid, pats in RULES.items()}


def match_pattern_ids(text: str) -> list[str]:
    hits = []
    for pid, regexes in _COMPILED.items():
        if any(r.search(text) for r in regexes):
            hits.append(pid)
    return hits


def main() -> None:
    docs = json.loads(KB_PATH.read_text(encoding="utf-8"))
    tagged = 0
    counts: dict[str, int] = {pid: 0 for pid in RULES}
    for doc in docs:
        text = f"{doc.get('title','')} {doc.get('content','')}"
        pids = match_pattern_ids(text)
        doc["pattern_ids"] = pids  # field moi, category cu giu nguyen
        if pids:
            tagged += 1
            for p in pids:
                counts[p] += 1

    KB_PATH.write_text(json.dumps(docs, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Tagged {tagged}/{len(docs)} docs voi it nhat 1 pattern_id")
    print(f"Untagged (pattern_ids=[]): {len(docs) - tagged}")
    print()
    for pid, n in sorted(counts.items(), key=lambda x: x[1]):
        print(f"  {n:4d}  {pid}")


if __name__ == "__main__":
    main()
