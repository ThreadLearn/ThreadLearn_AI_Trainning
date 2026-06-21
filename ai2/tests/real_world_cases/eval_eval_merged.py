"""
Eval ThreadLearn race_detector trên 20 real-world test cases.
Chạy từ thư mục ai2/:  python tests/real_world_cases/eval_real_world.py
"""
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "server"))
from race_detector import detectRaceConditions

CASES_PATH = os.path.join(os.path.dirname(__file__), "real_world_test_cases.json")

PATTERN_ALIASES = {
    "race_condition": ["closure_loop_var", "shared_var_settimeout", "concurrent_write_array",
                       "counter_no_atomic", "zalgo"],
    "toctou": ["closure_loop_var", "concurrent_write_array"],
    "double_callback": ["double_callback"],
    "zalgo": ["zalgo"],
    "event_loop_blocking": ["shared_var_settimeout"],
    "context_loss_this": ["context_loss_this"],
    "resource_exhaustion": ["resource_exhaustion"],
    "buffer_leak": ["buffer_leak"],
    "unhandled_rejection": ["unhandled_rejection", "promise_no_await"],
    "sequential_awaits": ["sequential_awaits"],
    "callback_hell": ["callback_hell"],
}


def check_detection(detections: list[dict], expected_patterns: list[str]) -> bool:
    found_ids = {d["pattern_id"] for d in detections}
    for ep in expected_patterns:
        aliases = PATTERN_ALIASES.get(ep, [ep])
        if found_ids & set(aliases):
            return True
    return False


def main():
    with open(CASES_PATH, encoding="utf-8") as f:
        cases = json.load(f)

    print("=" * 65)
    print("ThreadLearn race_detector — Real-World Benchmark (20 cases)")
    print("=" * 65)

    results = []
    detected = 0

    for tc in cases:
        detections = detectRaceConditions(tc["code"], "javascript")
        passed = check_detection(detections, tc["expected_patterns"])
        if passed:
            detected += 1
            icon = "DETECT"
        else:
            icon = "MISS  "

        found_ids = [d["pattern_id"] for d in detections] or ["(none)"]
        print(f"[{icon}] {tc['id']} | {tc['category']:<22} | {tc['package']}")
        if not passed:
            print(f"         expected: {tc['expected_patterns']}")
            print(f"         found:    {found_ids}")

        results.append({
            "id": tc["id"],
            "category": tc["category"],
            "package": tc["package"],
            "source": tc["source"],
            "detected": passed,
            "expected_patterns": tc["expected_patterns"],
            "found_patterns": [d["pattern_id"] for d in detections],
        })

    print("=" * 65)
    print(f"Detection rate: {detected}/20  ({detected/20*100:.0f}%)")
    print(f"Missed:         {20 - detected}/20")

    out_path = os.path.join(os.path.dirname(__file__), "eval_real_world_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "total": 20,
            "detected": detected,
            "missed": 20 - detected,
            "detection_rate": f"{detected/20*100:.0f}%",
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
