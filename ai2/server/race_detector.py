"""
AI2-03: Race Condition Detector
Owner: AI2 - Trung
Status: Done
Depends on: AI1-03 ast_preprocessor.py (Ân)

Phát hiện 10 race condition patterns trong JavaScript/Python bằng rule-based scan.
Input: code string + language → Output: list[dict] raw detections cho report_formatter.

Interface chính:
    detectRaceConditions(code, language) -> list[dict]

Mỗi detection dict:
    {
        "pattern_id": str,    # khớp _FIX_TEMPLATES trong report_formatter.py
        "line_range": str,    # "start-end" hoặc "line"
        "description": str,   # mô tả cụ thể, có tên biến/hàm
    }
"""

import re
import sys
import os

# Import ast_preprocessor từ AI1 (cùng được mount trong PYTHONPATH khi chạy server)
# Fallback regex nếu import fail (CI / test isolation)
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ai1", "modules"))
    from ast_preprocessor import extractFunctions, extract_keywords, stripComments
    _HAS_AST_PREPROCESSOR = True
except ImportError:
    _HAS_AST_PREPROCESSOR = False

    def extractFunctions(code: str, language: str = "javascript") -> list:  # type: ignore[misc]
        return []

    def extract_keywords(code: str, language: str = "javascript") -> str:  # type: ignore[misc]
        return ""

    def stripComments(code: str, language: str = "javascript") -> str:  # type: ignore[misc]
        code = re.sub(r'(?m)^\s*//.*$', '', code)
        code = re.sub(r'/\*[\s\S]*?\*/', '', code)
        return code


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lines(code: str) -> list[str]:
    return code.splitlines()


def _line_range(start: int, end: int | None = None) -> str:
    if end is None or end == start:
        return str(start)
    return f"{start}-{end}"


def _find_lines(code: str, pattern: re.Pattern) -> list[tuple[int, str]]:
    """Trả danh sách (line_number_1based, matched_line) cho pattern."""
    results = []
    for i, line in enumerate(_lines(code), 1):
        if pattern.search(line):
            results.append((i, line.strip()))
    return results


# ---------------------------------------------------------------------------
# Pattern detectors — mỗi hàm trả list[dict] raw detections
# ---------------------------------------------------------------------------

# JS Pattern 1: var trong for-loop + async callback (closure_loop_var)
_RE_FOR_VAR = re.compile(r'\bfor\s*\(\s*var\s+\w+')
_RE_ASYNC_CB = re.compile(r'\b(setTimeout|setInterval|Promise|\.then|addEventListener)\b')

def _detect_closure_loop_var(code: str) -> list[dict]:
    detections = []
    lines = _lines(code)
    for i, line in enumerate(lines, 1):
        if _RE_FOR_VAR.search(line):
            # Tìm async callback trong block tiếp theo (10 dòng)
            window = "\n".join(lines[i:i+10])
            if _RE_ASYNC_CB.search(window):
                # Tính end line của block
                end = min(i + 10, len(lines))
                detections.append({
                    "pattern_id": "closure_loop_var",
                    "line_range": _line_range(i, end),
                    "description": (
                        f"for-loop dùng var tại dòng {i} kết hợp với async callback "
                        f"— var không tạo block scope, mọi callback capture cùng biến."
                    ),
                })
    return detections


# JS Pattern 2: setTimeout/setInterval với biến var bên ngoài (shared_var_settimeout)
_RE_SETTIME = re.compile(r'\b(setTimeout|setInterval)\s*\(')
_RE_VAR_DECL = re.compile(r'\bvar\s+(\w+)')

def _detect_shared_var_settimeout(code: str) -> list[dict]:
    detections = []
    lines = _lines(code)
    # Tìm var declarations trong scope toàn file
    var_names: set[str] = set()
    for line in lines:
        for m in _RE_VAR_DECL.finditer(line):
            var_names.add(m.group(1))

    for i, line in enumerate(lines, 1):
        if _RE_SETTIME.search(line):
            # Kiểm tra callback body (5 dòng sau) dùng var đã khai báo không
            window = "\n".join(lines[i:i+5])
            for vname in var_names:
                if re.search(r'\b' + re.escape(vname) + r'\b', window):
                    detections.append({
                        "pattern_id": "shared_var_settimeout",
                        "line_range": _line_range(i, min(i+5, len(lines))),
                        "description": (
                            f"setTimeout tại dòng {i} có thể capture biến `{vname}` "
                            f"(khai báo bằng var) qua closure — giá trị bị thay đổi trước khi callback chạy."
                        ),
                    })
                    break  # 1 detection per setTimeout
    return detections


# JS Pattern 3: Promise không có await/catch (promise_no_await)
_RE_PROMISE_CALL = re.compile(r'\b\w+\s*\(.*\)\s*(?!\.then|\.catch|;?\s*//)(?:\n|$)')
_RE_ASYNC_FN = re.compile(r'\basync\s+function|\basync\s*\(|\basync\s+\w+\s*=>')
_RE_AWAIT = re.compile(r'\bawait\b')
_RE_PROMISE_NEW = re.compile(r'\bnew\s+Promise\s*\(')
_RE_FETCH = re.compile(r'\b(fetch|axios|http\.get|http\.post)\s*\(')

def _detect_promise_no_await(code: str) -> list[dict]:
    detections = []
    lines = _lines(code)
    in_async = False
    for i, line in enumerate(lines, 1):
        if _RE_ASYNC_FN.search(line):
            in_async = True
        if in_async and _RE_FETCH.search(line) and not _RE_AWAIT.search(line):
            # Kiểm tra không có .then() trên cùng dòng hoặc dòng tiếp
            next_line = lines[i] if i < len(lines) else ""
            if ".then" not in line and ".then" not in next_line and ".catch" not in line:
                detections.append({
                    "pattern_id": "promise_no_await",
                    "line_range": str(i),
                    "description": (
                        f"Dòng {i}: async call không có await hoặc .then()/.catch() "
                        f"— fire-and-forget có thể gây unhandled rejection."
                    ),
                })
    return detections


# JS Pattern 4: concurrent write vào cùng array/object (concurrent_write_array)
_RE_PUSH = re.compile(r'(\w+)\s*\.\s*push\s*\(')
_RE_ASSIGN_IDX = re.compile(r'(\w+)\s*\[.*\]\s*=')

def _detect_concurrent_write_array(code: str) -> list[dict]:
    detections = []
    lines = _lines(code)
    # Tìm tên array được push trong Promise.all / async context
    push_targets: dict[str, list[int]] = {}
    for i, line in enumerate(lines, 1):
        m = _RE_PUSH.search(line)
        if m:
            name = m.group(1)
            push_targets.setdefault(name, []).append(i)

    for name, line_nums in push_targets.items():
        if len(line_nums) >= 2:
            # Kiểm tra có async context không
            window_start = max(0, line_nums[0] - 5)
            window = "\n".join(lines[window_start:line_nums[-1]])
            if _RE_ASYNC_CB.search(window) or "Promise" in window:
                detections.append({
                    "pattern_id": "concurrent_write_array",
                    "line_range": _line_range(line_nums[0], line_nums[-1]),
                    "description": (
                        f"Array `{name}` bị push từ nhiều async callback "
                        f"(dòng {', '.join(str(l) for l in line_nums)}) "
                        f"— có thể gây race condition nếu callbacks chạy song song."
                    ),
                })
    return detections


# Python Pattern 5: global variable trong thread function (global_var_thread)
_RE_THREAD_START = re.compile(r'\bthreading\.Thread\s*\(|Thread\s*\(target\s*=')
_RE_GLOBAL_KW = re.compile(r'\bglobal\s+(\w+)')

def _detect_global_var_thread(code: str) -> list[dict]:
    detections = []
    lines = _lines(code)
    global_vars: set[str] = set()
    for line in lines:
        m = _RE_GLOBAL_KW.search(line)
        if m:
            global_vars.add(m.group(1))

    for i, line in enumerate(lines, 1):
        if _RE_THREAD_START.search(line):
            # Check surrounding code uses global vars
            window = "\n".join(lines[max(0, i-5):i+10])
            for vname in global_vars:
                if re.search(r'\b' + re.escape(vname) + r'\b', window):
                    detections.append({
                        "pattern_id": "global_var_thread",
                        "line_range": _line_range(max(1, i-2), min(i+5, len(lines))),
                        "description": (
                            f"Thread tại dòng {i} truy cập biến global `{vname}` "
                            f"không có Lock — có thể gây data race."
                        ),
                    })
                    break
    return detections


# Python Pattern 6: shared list không có Lock (shared_list_no_lock)
_RE_LIST_APPEND = re.compile(r'(\w+)\s*\.\s*append\s*\(')
_RE_LOCK = re.compile(r'\bLock\(\)|RLock\(\)|with\s+\w+.*lock', re.IGNORECASE)

def _detect_shared_list_no_lock(code: str) -> list[dict]:
    detections = []
    lines = _lines(code)
    has_lock = bool(_RE_LOCK.search(code))
    if has_lock:
        return []  # Nếu có Lock ở bất kỳ đâu → không flag

    append_targets: dict[str, list[int]] = {}
    for i, line in enumerate(lines, 1):
        m = _RE_LIST_APPEND.search(line)
        if m:
            name = m.group(1)
            append_targets.setdefault(name, []).append(i)

    if _RE_THREAD_START.search(code):
        for name, line_nums in append_targets.items():
            if len(line_nums) >= 2:
                detections.append({
                    "pattern_id": "shared_list_no_lock",
                    "line_range": _line_range(line_nums[0], line_nums[-1]),
                    "description": (
                        f"List `{name}` được append từ nhiều thread "
                        f"(dòng {', '.join(str(l) for l in line_nums)}) "
                        f"mà không có Lock."
                    ),
                })
    return detections


# Python Pattern 7: thread read-write race (thread_read_write_race)
_RE_THREAD_FN = re.compile(r'def\s+(\w+).*:')

def _detect_thread_read_write_race(code: str) -> list[dict]:
    detections = []
    if not _RE_THREAD_START.search(code):
        return []
    has_lock = bool(_RE_LOCK.search(code))
    if has_lock:
        return []

    lines = _lines(code)
    # Tìm assignment vào shared variable trong thread functions
    shared_vars: dict[str, list[int]] = {}
    for i, line in enumerate(lines, 1):
        m = re.search(r'^(\s{4,}|\t)(\w+)\s*[+\-*]?=\s*', line)
        if m:
            name = m.group(2)
            if name not in ('self', 'cls', 'True', 'False', 'None'):
                shared_vars.setdefault(name, []).append(i)

    for name, line_nums in shared_vars.items():
        if len(line_nums) >= 2:
            detections.append({
                "pattern_id": "thread_read_write_race",
                "line_range": _line_range(line_nums[0], line_nums[-1]),
                "description": (
                    f"Biến `{name}` bị ghi từ nhiều vị trí trong thread context "
                    f"(dòng {', '.join(str(l) for l in line_nums[:3])}) "
                    f"mà không có Lock."
                ),
            })
    return detections[:3]  # Giới hạn 3 để tránh noise


# Python Pattern 8: thiếu thread.join() (missing_join)
_RE_THREAD_ASSIGN = re.compile(r'(\w+)\s*=\s*(?:threading\.)?Thread\s*\(')
_RE_JOIN = re.compile(r'\.join\s*\(')

def _detect_missing_join(code: str) -> list[dict]:
    detections = []
    lines = _lines(code)
    thread_vars: dict[str, int] = {}
    for i, line in enumerate(lines, 1):
        m = _RE_THREAD_ASSIGN.search(line)
        if m:
            thread_vars[m.group(1)] = i

    if not thread_vars:
        return []

    joined_vars: set[str] = set()
    for line in lines:
        for vname in thread_vars:
            if re.search(r'\b' + re.escape(vname) + r'\b', line) and _RE_JOIN.search(line):
                joined_vars.add(vname)

    for vname, start_line in thread_vars.items():
        if vname not in joined_vars:
            detections.append({
                "pattern_id": "missing_join",
                "line_range": str(start_line),
                "description": (
                    f"Thread `{vname}` (dòng {start_line}) được tạo nhưng không có .join() "
                    f"— main thread có thể đọc kết quả trước khi thread hoàn thành."
                ),
            })
    return detections


# Python Pattern 9: singleton lazy init không có Lock (singleton_lazy_init)
_RE_NONE_CHECK = re.compile(r'if\s+\w+\s+is\s+None\s*:')
_RE_INSTANCE_ASSIGN = re.compile(r'(\w+)\s*=\s*\w+\s*\(')

def _detect_singleton_lazy_init(code: str) -> list[dict]:
    detections = []
    if not _RE_THREAD_START.search(code):
        return []
    has_lock = bool(_RE_LOCK.search(code))
    if has_lock:
        return []

    lines = _lines(code)
    for i, line in enumerate(lines, 1):
        if _RE_NONE_CHECK.search(line):
            next_lines = "\n".join(lines[i:i+3])
            if _RE_INSTANCE_ASSIGN.search(next_lines):
                detections.append({
                    "pattern_id": "singleton_lazy_init",
                    "line_range": _line_range(i, min(i+3, len(lines))),
                    "description": (
                        f"Lazy initialization tại dòng {i} không có Lock "
                        f"— race condition nếu nhiều thread khởi tạo cùng lúc (TOCTOU)."
                    ),
                })
    return detections


# JS/Python Pattern 10: counter không atomic (counter_no_atomic)
_RE_INCREMENT = re.compile(r'\b(\w+)\s*\+\+|\b(\w+)\s*\+=\s*1|\b(\w+)\s*=\s*\2\s*\+\s*1')
_RE_COUNTER_VAR = re.compile(r'\b(\w+)\s*(?:\+\+|\+=\s*1)')

def _detect_counter_no_atomic(code: str) -> list[dict]:
    detections = []
    lines = _lines(code)
    # Chỉ flag nếu có async context
    has_async = bool(_RE_ASYNC_CB.search(code) or _RE_THREAD_START.search(code))
    if not has_async:
        return []

    counter_vars: dict[str, list[int]] = {}
    for i, line in enumerate(lines, 1):
        m = _RE_COUNTER_VAR.search(line)
        if m:
            name = m.group(1)
            counter_vars.setdefault(name, []).append(i)

    for name, line_nums in counter_vars.items():
        if len(line_nums) >= 2:
            detections.append({
                "pattern_id": "counter_no_atomic",
                "line_range": _line_range(line_nums[0], line_nums[-1]),
                "description": (
                    f"Counter `{name}` bị increment tại nhiều điểm "
                    f"(dòng {', '.join(str(l) for l in line_nums)}) "
                    f"trong async/concurrent context — read-modify-write không atomic."
                ),
            })
    return detections


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_JS_DETECTORS = [
    _detect_closure_loop_var,
    _detect_shared_var_settimeout,
    _detect_promise_no_await,
    _detect_concurrent_write_array,
    _detect_counter_no_atomic,
]

_PY_DETECTORS = [
    _detect_global_var_thread,
    _detect_shared_list_no_lock,
    _detect_thread_read_write_race,
    _detect_missing_join,
    _detect_singleton_lazy_init,
    _detect_counter_no_atomic,
]


def detectRaceConditions(code: str, language: str = "javascript") -> list[dict]:
    """
    Phát hiện race condition patterns trong code.

    Args:
        code:     source code string
        language: "javascript" | "typescript" | "python"

    Returns:
        list[dict] raw detections — truyền thẳng vào report_formatter.format_report()
        Rỗng nếu không phát hiện vấn đề.

    Ví dụ:
        detections = detectRaceConditions(js_code, "javascript")
        issues = format_report(detections)
    """
    lang = language.lower()
    if lang == "typescript":
        lang = "javascript"

    # Strip comments trước khi scan (dùng ast_preprocessor nếu có)
    clean_code = stripComments(code, lang)

    if lang == "javascript":
        detectors = _JS_DETECTORS
    elif lang == "python":
        detectors = _PY_DETECTORS
    else:
        return []

    raw: list[dict] = []
    for detector in detectors:
        raw.extend(detector(clean_code))

    # Dedup: bỏ detection trùng pattern_id + line_range
    seen: set[tuple] = set()
    unique: list[dict] = []
    for d in raw:
        key = (d["pattern_id"], d["line_range"])
        if key not in seen:
            seen.add(key)
            unique.append(d)

    return unique
