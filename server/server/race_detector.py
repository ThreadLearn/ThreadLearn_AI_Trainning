"""
AI2-03: Race Condition Detector
Owner: AI2 - Trung
Status: Done
Depends on: AI1-03 ast_preprocessor.py (Ân)

Phát hiện 10 race condition patterns trong JavaScript bằng rule-based scan.
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
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "training", "modules"))
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


# JS Pattern 5: counter không atomic (counter_no_atomic)
_RE_INCREMENT = re.compile(r'\b(\w+)\s*\+\+|\b(\w+)\s*\+=\s*1|\b(\w+)\s*=\s*\2\s*\+\s*1')
_RE_COUNTER_VAR = re.compile(r'\b(\w+)\s*(?:\+\+|\+=\s*1)')

def _detect_counter_no_atomic(code: str) -> list[dict]:
    detections = []
    lines = _lines(code)
    # Chỉ flag nếu có async context
    has_async = bool(_RE_ASYNC_CB.search(code) or _RE_ASYNC_FN.search(code))
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


# JS Pattern 6: .then() không có .catch() (unhandled_rejection)
_RE_THEN = re.compile(r'\.then\s*\(')
_RE_CATCH = re.compile(r'\.catch\s*\(')
_RE_TRY = re.compile(r'\btry\s*\{')

def _detect_unhandled_rejection(code: str) -> list[dict]:
    detections = []
    lines = _lines(code)
    for i, line in enumerate(lines, 1):
        if _RE_THEN.search(line):
            # Tìm .catch trong 5 dòng tiếp theo
            window = "\n".join(lines[i:i+5])
            if not _RE_CATCH.search(window) and not _RE_CATCH.search(line):
                # Kiểm tra không có try/catch bao ngoài (10 dòng trước)
                outer = "\n".join(lines[max(0, i-10):i])
                if not _RE_TRY.search(outer):
                    detections.append({
                        "pattern_id": "unhandled_rejection",
                        "line_range": str(i),
                        "description": (
                            f"Dòng {i}: .then() không có .catch() — "
                            f"Promise rejection không được bắt, gây unhandled rejection."
                        ),
                    })
    return detections


# JS Pattern 7: callback bị gọi nhiều lần (double_callback)
_RE_CB_CALL = re.compile(r'\b(cb|callback|next|done)\s*\(')
_RE_RETURN_CB = re.compile(r'\breturn\s+(cb|callback|next|done)\s*\(')

def _detect_double_callback(code: str) -> list[dict]:
    detections = []
    lines = _lines(code)
    i = 0
    while i < len(lines):
        # Tìm function có cb/callback parameter
        fn_match = re.search(r'function.*\b(cb|callback|next|done)\b', lines[i])
        if fn_match:
            cb_name = fn_match.group(1)
            re_cb = re.compile(r'\b' + cb_name + r'\s*\(')
            re_ret_cb = re.compile(r'\breturn\s+' + cb_name + r'\s*\(')
            # Tìm body của function (30 dòng tiếp)
            body_lines = lines[i+1:i+30]
            cb_calls = []
            for j, bline in enumerate(body_lines, i+2):
                if re_cb.search(bline) and not re_ret_cb.search(bline):
                    cb_calls.append(j)
            if len(cb_calls) >= 2:
                detections.append({
                    "pattern_id": "double_callback",
                    "line_range": _line_range(cb_calls[0], cb_calls[-1]),
                    "description": (
                        f"`{cb_name}` bị gọi nhiều lần (dòng {', '.join(str(l) for l in cb_calls)}) "
                        f"mà không có return — callback fired multiple times."
                    ),
                })
        i += 1
    return detections


# JS Pattern 8: zalgo — callback gọi cả sync lẫn async (zalgo)
def _detect_zalgo(code: str) -> list[dict]:
    detections = []
    lines = _lines(code)
    for i, line in enumerate(lines, 1):
        fn_match = re.search(r'function.*\b(cb|callback)\b', line)
        if fn_match:
            cb_name = fn_match.group(1)
            body = lines[i:i+20]
            sync_call = False
            async_call = False
            sync_line = async_line = 0
            for j, bline in enumerate(body, i+1):
                has_cb = re.search(r'\b' + cb_name + r'\s*\(', bline)
                if not has_cb:
                    continue
                is_async = bool(_RE_ASYNC_CB.search(bline) or re.search(r'\.then\s*\(', bline))
                if is_async:
                    async_call = True
                    async_line = j
                else:
                    sync_call = True
                    sync_line = j
            if sync_call and async_call:
                detections.append({
                    "pattern_id": "zalgo",
                    "line_range": _line_range(sync_line, async_line),
                    "description": (
                        f"`{cb_name}` được gọi sync (dòng {sync_line}) lẫn async (dòng {async_line}) "
                        f"— hành vi không nhất quán (Zalgo anti-pattern)."
                    ),
                })
    return detections


# JS Pattern 9: this mất context trong setTimeout/setInterval (context_loss_this)
_RE_THIS = re.compile(r'\bthis\b')
_RE_REGULAR_FN = re.compile(r'\bfunction\s*\(')

def _detect_context_loss_this(code: str) -> list[dict]:
    detections = []
    lines = _lines(code)
    for i, line in enumerate(lines, 1):
        if _RE_SETTIME.search(line) and _RE_REGULAR_FN.search(line):
            # Tìm this trong body callback (10 dòng tiếp)
            window = "\n".join(lines[i:i+10])
            if _RE_THIS.search(window):
                detections.append({
                    "pattern_id": "context_loss_this",
                    "line_range": _line_range(i, min(i+5, len(lines))),
                    "description": (
                        f"setTimeout/setInterval tại dòng {i} dùng function() thường có `this` "
                        f"— this sẽ là undefined hoặc global. Dùng arrow function hoặc .bind(this)."
                    ),
                })
    return detections


# JS Pattern 10: callback hell — lồng nhau >= 3 cấp (callback_hell)
def _detect_callback_hell(code: str) -> list[dict]:
    detections = []
    lines = _lines(code)
    max_depth = 0
    max_line = 0
    depth = 0
    for i, line in enumerate(lines, 1):
        # Đếm arrow/function callbacks mở
        opens = len(re.findall(r'=>\s*\{|\bfunction\s*\w*\s*\([^)]*\)\s*\{', line))
        closes = line.count('}')
        depth += opens - closes
        if depth > max_depth:
            max_depth = depth
            max_line = i
    if max_depth >= 3:
        detections.append({
            "pattern_id": "callback_hell",
            "line_range": str(max_line),
            "description": (
                f"Callback lồng nhau {max_depth} cấp (sâu nhất tại dòng {max_line}) "
                f"— khó đọc, khó debug. Refactor sang async/await hoặc Promise chain."
            ),
        })
    return detections


# JS Pattern 11: Promise.all không giới hạn concurrency (resource_exhaustion)
_RE_PROMISE_ALL = re.compile(r'Promise\.all\s*\(')
_RE_MAP = re.compile(r'\.map\s*\(')

def _detect_resource_exhaustion(code: str) -> list[dict]:
    detections = []
    lines = _lines(code)
    for i, line in enumerate(lines, 1):
        if _RE_PROMISE_ALL.search(line):
            # Tìm .map( trên cùng dòng hoặc 3 dòng trước
            window = "\n".join(lines[max(0, i-3):i+1])
            if _RE_MAP.search(window):
                detections.append({
                    "pattern_id": "resource_exhaustion",
                    "line_range": str(i),
                    "description": (
                        f"Promise.all() tại dòng {i} với .map() không giới hạn concurrency "
                        f"— có thể tạo hàng nghìn request/connection cùng lúc. "
                        f"Dùng p-limit hoặc chunk array."
                    ),
                })
    return detections


# JS Pattern 12: sequential awaits có thể parallel hóa (sequential_awaits)
_RE_AWAIT_LINE = re.compile(r'\bawait\b')

def _detect_sequential_awaits(code: str) -> list[dict]:
    detections = []
    lines = _lines(code)
    i = 0
    while i < len(lines):
        if _RE_ASYNC_FN.search(lines[i]):
            # Đếm await liên tiếp trong 20 dòng tiếp
            await_lines = []
            await_args = []
            for j in range(i+1, min(i+20, len(lines))):
                if _RE_AWAIT_LINE.search(lines[j]):
                    await_lines.append(j+1)
                    # Lấy argument của await call
                    m = re.search(r'await\s+\w+\.\w+\(([^)]*)\)', lines[j])
                    if m:
                        await_args.append(m.group(1).strip())
                elif lines[j].strip() and not lines[j].strip().startswith('//'):
                    if len(await_lines) >= 3:
                        break
                    await_lines = []
                    await_args = []
            if len(await_lines) >= 3:
                # Kiểm tra các await call dùng cùng argument → độc lập
                unique_args = set(await_args)
                if len(unique_args) == 1 and list(unique_args)[0]:
                    detections.append({
                        "pattern_id": "sequential_awaits",
                        "line_range": _line_range(await_lines[0], await_lines[-1]),
                        "description": (
                            f"{len(await_lines)} await liên tiếp (dòng {await_lines[0]}–{await_lines[-1]}) "
                            f"với cùng argument — có thể chạy song song bằng Promise.all()."
                        ),
                    })
        i += 1
    return detections


# JS Pattern 13: stream pipe không handle error (buffer_leak)
_RE_PIPE = re.compile(r'\.pipe\s*\(')
_RE_ON_ERROR = re.compile(r'\.on\s*\(\s*[\'"]error[\'"]')
_RE_DESTROY = re.compile(r'\.destroy\s*\(')

def _detect_buffer_leak(code: str) -> list[dict]:
    detections = []
    lines = _lines(code)
    for i, line in enumerate(lines, 1):
        if _RE_PIPE.search(line):
            # Tìm .on('error') hoặc .destroy() trong 10 dòng xung quanh
            window = "\n".join(lines[max(0, i-5):i+10])
            if not _RE_ON_ERROR.search(window) and not _RE_DESTROY.search(window):
                detections.append({
                    "pattern_id": "buffer_leak",
                    "line_range": str(i),
                    "description": (
                        f".pipe() tại dòng {i} không có .on('error') handler "
                        f"— nếu stream lỗi, pipe không tự đóng → memory/fd leak."
                    ),
                })
    return detections


# JS Pattern 14: sync I/O (readFileSync/execSync/...) inside async route/handler (sync_io_blocking)
_RE_SYNC_IO = re.compile(r'\b(fs\.)?(readFileSync|writeFileSync|appendFileSync|existsSync|statSync|execSync|readdirSync)\s*\(')
_RE_ASYNC_HANDLER = re.compile(r'\basync\s*(?:function\s*\w*\s*\(|\([^)]*\)\s*=>|\w+\s*=>)')

def _detect_sync_io_blocking(code: str) -> list[dict]:
    detections = []
    lines = _lines(code)
    in_async_depth: list[int] = []  # brace-depth stack tại điểm mở async function
    depth = 0
    for i, line in enumerate(lines, 1):
        opens = line.count('{')
        closes = line.count('}')

        if _RE_ASYNC_HANDLER.search(line):
            # Scope thân hàm bắt đầu ở depth sau khi cộng '{' của chính dòng khai báo.
            in_async_depth.append(depth + opens)

        m = _RE_SYNC_IO.search(line)
        if m and in_async_depth:
            fname = m.group(2)
            detections.append({
                "pattern_id": "sync_io_blocking",
                "line_range": str(i),
                "description": (
                    f"`{fname}` (dòng {i}) là sync I/O gọi bên trong async handler "
                    f"— block toàn bộ Node.js event loop, mọi request khác phải chờ."
                ),
            })

        depth += opens - closes
        # Đóng scope async khi depth tụt xuống dưới mức thân hàm đã mở.
        while in_async_depth and depth < in_async_depth[-1]:
            in_async_depth.pop()

    return detections


# ---------------------------------------------------------------------------
# Python Pattern 1: global var mutated inside threading.Thread target (global_var_thread)
# ---------------------------------------------------------------------------
_RE_PY_GLOBAL = re.compile(r'\bglobal\s+(\w+)')
_RE_PY_THREAD = re.compile(r'\bthreading\.Thread\s*\(')
_RE_PY_LOCK_WITH = re.compile(r'\bwith\s+\w*lock\w*\s*:', re.IGNORECASE)

def _detect_global_var_thread(code: str) -> list[dict]:
    detections = []
    lines = _lines(code)
    if not _RE_PY_THREAD.search(code):
        return detections
    seen_names: set[str] = set()
    for i, line in enumerate(lines, 1):
        m = _RE_PY_GLOBAL.search(line)
        if not m:
            continue
        name = m.group(1)
        if name in seen_names:
            continue
        # Bỏ qua nếu function body (20 dòng tiếp) được bảo vệ bởi `with lock:`
        window = "\n".join(lines[i:i+20])
        if _RE_PY_LOCK_WITH.search(window):
            continue
        seen_names.add(name)
        detections.append({
            "pattern_id": "global_var_thread",
            "line_range": str(i),
            "description": (
                f"Biến global `{name}` (dòng {i}) bị mutate trong hàm chạy qua threading.Thread "
                f"— không có lock bảo vệ, nhiều thread ghi đồng thời gây race condition."
            ),
        })
    return detections


# Python Pattern 2: shared list bị nhiều thread append không lock (shared_list_no_lock)
_RE_PY_LIST_APPEND = re.compile(r'(\w+)\s*\.\s*append\s*\(')

def _detect_shared_list_no_lock(code: str) -> list[dict]:
    detections = []
    lines = _lines(code)
    if not _RE_PY_THREAD.search(code):
        return detections

    append_targets: dict[str, list[int]] = {}
    for i, line in enumerate(lines, 1):
        m = _RE_PY_LIST_APPEND.search(line)
        if m:
            append_targets.setdefault(m.group(1), []).append(i)

    for name, line_nums in append_targets.items():
        if len(line_nums) < 2:
            continue
        window_start = max(0, line_nums[0] - 5)
        window = "\n".join(lines[window_start:line_nums[-1] + 5])
        if _RE_PY_LOCK_WITH.search(window):
            continue
        detections.append({
            "pattern_id": "shared_list_no_lock",
            "line_range": _line_range(line_nums[0], line_nums[-1]),
            "description": (
                f"List `{name}` bị append từ code chạy trong nhiều threading.Thread "
                f"(dòng {', '.join(str(l) for l in line_nums)}) mà không có `with lock:` bảo vệ."
            ),
        })
    return detections


# Python Pattern 3: Thread.start() không có join() tương ứng (missing_join)
_RE_PY_THREAD_VAR = re.compile(r'(\w+)\s*=\s*threading\.Thread\s*\(')
_RE_PY_START = re.compile(r'(\w+)\s*\.\s*start\s*\(\s*\)')
_RE_PY_JOIN = re.compile(r'(\w+)\s*\.\s*join\s*\(\s*\)')

def _detect_missing_join(code: str) -> list[dict]:
    detections = []
    lines = _lines(code)
    started: dict[str, int] = {}
    joined: set[str] = set()
    for i, line in enumerate(lines, 1):
        m_start = _RE_PY_START.search(line)
        if m_start:
            started.setdefault(m_start.group(1), i)
        m_join = _RE_PY_JOIN.search(line)
        if m_join:
            joined.add(m_join.group(1))

    for name, line_no in started.items():
        if name not in joined:
            detections.append({
                "pattern_id": "missing_join",
                "line_range": str(line_no),
                "description": (
                    f"Thread `{name}` được start() tại dòng {line_no} nhưng không có `{name}.join()` "
                    f"— chương trình có thể kết thúc trước khi thread hoàn tất, kết quả không xác định."
                ),
            })
    return detections


# Python Pattern 4: lazy singleton init không thread-safe (singleton_lazy_init)
_RE_PY_IF_NONE = re.compile(r'\bif\s+(\w+)\s+is\s+None\s*:')

def _detect_singleton_lazy_init(code: str) -> list[dict]:
    detections = []
    lines = _lines(code)
    if not _RE_PY_THREAD.search(code) and not _RE_PY_GLOBAL.search(code):
        return detections
    for i, line in enumerate(lines, 1):
        m = _RE_PY_IF_NONE.search(line)
        if not m:
            continue
        name = m.group(1)
        window = "\n".join(lines[i:i+5])
        if re.search(r'\b' + re.escape(name) + r'\s*=', window):
            window_lock = "\n".join(lines[max(0, i-5):i+5])
            if _RE_PY_LOCK_WITH.search(window_lock):
                continue
            detections.append({
                "pattern_id": "singleton_lazy_init",
                "line_range": _line_range(i, min(i + 5, len(lines))),
                "description": (
                    f"Lazy init `{name}` tại dòng {i} kiểm tra `is None` rồi gán mà không lock "
                    f"— hai thread có thể cùng qua check và tạo instance hai lần (double-checked locking bug)."
                ),
            })
    return detections


_PY_DETECTORS = [
    _detect_global_var_thread,
    _detect_shared_list_no_lock,
    _detect_missing_join,
    _detect_singleton_lazy_init,
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_JS_DETECTORS = [
    _detect_closure_loop_var,
    _detect_shared_var_settimeout,
    _detect_promise_no_await,
    _detect_concurrent_write_array,
    _detect_counter_no_atomic,
    _detect_unhandled_rejection,
    _detect_double_callback,
    _detect_zalgo,
    _detect_context_loss_this,
    _detect_callback_hell,
    _detect_resource_exhaustion,
    _detect_sequential_awaits,
    _detect_buffer_leak,
    _detect_sync_io_blocking,
]


def detectRaceConditions(code: str, language: str = "javascript") -> list[dict]:
    """
    Phát hiện race condition patterns trong JavaScript/TypeScript.

    Args:
        code:     source code string
        language: "javascript" | "typescript"

    Returns:
        list[dict] raw detections — truyền thẳng vào report_formatter.format_report()
        Rỗng nếu không phát hiện vấn đề.

    Ví dụ:
        detections = detectRaceConditions(js_code, "javascript")
        issues = format_report(detections)
    """
    lang = language.lower()
    if lang not in ("javascript", "typescript", "python"):
        return []

    if lang == "python":
        clean_code = re.sub(r'(?m)^\s*#.*$', '', code)
        detectors = _PY_DETECTORS
    else:
        clean_code = stripComments(code, "javascript")
        detectors = _JS_DETECTORS

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


def count_patterns_checked(language: str = "javascript") -> int:
    """Số lượng pattern detector chạy qua cho ngôn ngữ này — dùng để hiện
    'quét N loại lỗi, phát hiện M vấn đề' ở FE, độc lập với số issue tìm thấy."""
    lang = language.lower()
    if lang == "python":
        return len(_PY_DETECTORS)
    if lang in ("javascript", "typescript"):
        return len(_JS_DETECTORS)
    return 0
