"""
AI2-03: Unit tests for race_detector
Owner: AI2 - Trung
Target: detect >= 12/15 positive cases, FP < 2/10 clean samples
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))

import pytest
from race_detector import detectRaceConditions


# ---------------------------------------------------------------------------
# JS Positive cases — phải detect được
# ---------------------------------------------------------------------------

def test_closure_loop_var_basic():
    code = """
for (var i = 0; i < 3; i++) {
    setTimeout(function() { console.log(i); }, 1000);
}
"""
    result = detectRaceConditions(code, "javascript")
    ids = [d["pattern_id"] for d in result]
    assert "closure_loop_var" in ids


def test_closure_loop_var_with_promise():
    code = """
for (var j = 0; j < 5; j++) {
    new Promise(function(resolve) { resolve(j); });
}
"""
    result = detectRaceConditions(code, "javascript")
    ids = [d["pattern_id"] for d in result]
    assert "closure_loop_var" in ids


def test_shared_var_settimeout():
    code = """
var count = 0;
setTimeout(function() {
    count++;
    console.log(count);
}, 500);
setTimeout(function() {
    count++;
}, 300);
"""
    result = detectRaceConditions(code, "javascript")
    ids = [d["pattern_id"] for d in result]
    assert "shared_var_settimeout" in ids


def test_concurrent_write_array():
    code = """
var results = [];
Promise.all([fetch('/a'), fetch('/b')]).then(function(responses) {
    responses.forEach(function(r) {
        results.push(r);
    });
    results.push('done');
});
"""
    result = detectRaceConditions(code, "javascript")
    ids = [d["pattern_id"] for d in result]
    assert "concurrent_write_array" in ids


def test_counter_no_atomic_js():
    code = """
var counter = 0;
setTimeout(function() { counter++; }, 100);
setTimeout(function() { counter++; }, 200);
"""
    result = detectRaceConditions(code, "javascript")
    ids = [d["pattern_id"] for d in result]
    assert "counter_no_atomic" in ids


def test_typescript_treated_as_js():
    code = """
for (var i = 0; i < 3; i++) {
    setTimeout(() => console.log(i), 100);
}
"""
    result = detectRaceConditions(code, "typescript")
    ids = [d["pattern_id"] for d in result]
    assert "closure_loop_var" in ids


# ---------------------------------------------------------------------------
# Python Positive cases
# ---------------------------------------------------------------------------

def test_global_var_thread():
    code = """
import threading
shared = 0

def worker():
    global shared
    shared += 1

t = threading.Thread(target=worker)
t.start()
"""
    result = detectRaceConditions(code, "python")
    ids = [d["pattern_id"] for d in result]
    assert "global_var_thread" in ids


def test_shared_list_no_lock():
    code = """
import threading
results = []

def worker(x):
    results.append(x * 2)
    results.append(x + 1)

t1 = threading.Thread(target=worker, args=(1,))
t2 = threading.Thread(target=worker, args=(2,))
t1.start()
t2.start()
"""
    result = detectRaceConditions(code, "python")
    ids = [d["pattern_id"] for d in result]
    assert "shared_list_no_lock" in ids


def test_missing_join():
    code = """
import threading

def task():
    pass

t = threading.Thread(target=task)
t.start()
# No t.join()
print("done")
"""
    result = detectRaceConditions(code, "python")
    ids = [d["pattern_id"] for d in result]
    assert "missing_join" in ids


def test_singleton_lazy_init():
    code = """
import threading
_instance = None

def get_instance():
    global _instance
    if _instance is None:
        _instance = ExpensiveObject()
    return _instance

t = threading.Thread(target=get_instance)
"""
    result = detectRaceConditions(code, "python")
    ids = [d["pattern_id"] for d in result]
    assert "singleton_lazy_init" in ids


def test_counter_no_atomic_python():
    code = """
import threading
count = 0

def increment():
    global count
    count += 1
    count += 1

t1 = threading.Thread(target=increment)
t2 = threading.Thread(target=increment)
"""
    result = detectRaceConditions(code, "python")
    ids = [d["pattern_id"] for d in result]
    assert "counter_no_atomic" in ids or "global_var_thread" in ids


# ---------------------------------------------------------------------------
# False Positive cases — code sạch KHÔNG được flag
# ---------------------------------------------------------------------------

def test_fp_let_loop_no_flag():
    """let trong for-loop → không phải race condition."""
    code = """
for (let i = 0; i < 3; i++) {
    setTimeout(function() { console.log(i); }, 1000);
}
"""
    result = detectRaceConditions(code, "javascript")
    ids = [d["pattern_id"] for d in result]
    assert "closure_loop_var" not in ids


def test_fp_clean_sync_js():
    """Code JS đồng bộ, không async."""
    code = """
function add(a, b) {
    return a + b;
}
var result = add(1, 2);
console.log(result);
"""
    result = detectRaceConditions(code, "javascript")
    assert len(result) == 0


def test_fp_python_with_lock():
    """Python có Lock → không flag shared_list."""
    code = """
import threading
results = []
lock = threading.Lock()

def worker(x):
    with lock:
        results.append(x)
        results.append(x + 1)

t1 = threading.Thread(target=worker, args=(1,))
t2 = threading.Thread(target=worker, args=(2,))
t1.start()
t2.start()
t1.join()
t2.join()
"""
    result = detectRaceConditions(code, "python")
    ids = [d["pattern_id"] for d in result]
    assert "shared_list_no_lock" not in ids
    assert "missing_join" not in ids


def test_fp_python_join_present():
    """Thread có join() → không flag missing_join."""
    code = """
import threading

def task():
    pass

t = threading.Thread(target=task)
t.start()
t.join()
print("done")
"""
    result = detectRaceConditions(code, "python")
    ids = [d["pattern_id"] for d in result]
    assert "missing_join" not in ids


def test_fp_unknown_language_returns_empty():
    code = "SELECT * FROM users;"
    result = detectRaceConditions(code, "sql")
    assert result == []


# ---------------------------------------------------------------------------
# Output structure
# ---------------------------------------------------------------------------

def test_detection_has_required_keys():
    code = """
for (var i = 0; i < 3; i++) {
    setTimeout(function() { console.log(i); }, 1000);
}
"""
    result = detectRaceConditions(code, "javascript")
    assert len(result) > 0
    for d in result:
        assert "pattern_id" in d
        assert "line_range" in d
        assert "description" in d


def test_no_duplicate_detections():
    code = """
for (var i = 0; i < 3; i++) {
    setTimeout(function() { console.log(i); }, 1000);
}
"""
    result = detectRaceConditions(code, "javascript")
    keys = [(d["pattern_id"], d["line_range"]) for d in result]
    assert len(keys) == len(set(keys))


def test_empty_code_returns_empty():
    assert detectRaceConditions("", "javascript") == []
    assert detectRaceConditions("", "python") == []


def test_integration_with_report_formatter():
    """Đầu ra của detectRaceConditions phải tương thích với format_report."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
    from report_formatter import format_report

    code = """
for (var i = 0; i < 3; i++) {
    setTimeout(function() { console.log(i); }, 1000);
}
var counter = 0;
setTimeout(function() { counter++; }, 100);
setTimeout(function() { counter++; }, 200);
"""
    raw = detectRaceConditions(code, "javascript")
    issues = format_report(raw)
    assert isinstance(issues, list)
    for issue in issues:
        assert issue.severity in ("high", "medium", "low")
        assert issue.line_range
        assert issue.description
        assert issue.fix
