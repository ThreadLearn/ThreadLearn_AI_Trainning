"""
AI2-04: Race Condition Report Formatter.

Nhận raw detections từ race_detector.py → format thành List[Issue] chuẩn API.

Output schema mỗi item:
    {line_range, severity, description, fix}

Severity rules:
    high   — deterministic failure: xảy ra hầu như mọi lần, crash/data corruption
    medium — timing-dependent, reproducible dưới concurrent load
    low    — hiếm, chỉ xảy ra trong điều kiện timing đặc biệt

Sort: high → medium → low, cùng severity sort theo line_range[0] tăng dần.
"""

from typing import Any

from schemas import Issue

# ---------------------------------------------------------------------------
# Fix templates — mỗi pattern ID → fix suggestion cố định
# ---------------------------------------------------------------------------

_FIX_TEMPLATES: dict[str, str] = {
    "shared_var_settimeout": (
        "Dùng closure với let hoặc const thay vì var để tạo binding riêng mỗi iteration. "
        "Hoặc dùng Promise/async-await để đảm bảo thứ tự thực thi."
    ),
    "promise_no_await": (
        "Thêm await trước Promise call, hoặc chain .then()/.catch() để bắt lỗi. "
        "Fire-and-forget Promise có thể gây unhandled rejection."
    ),
    "concurrent_write_array": (
        "Dùng Promise.all() nếu cần kết quả song song, hoặc dùng reduce/queue "
        "để serialize các write operation vào cùng array/object."
    ),
    "closure_loop_var": (
        "Thay var bằng let trong for-loop head — let tạo binding mới mỗi iteration. "
        "Hoặc wrap callback trong IIFE: (function(i) { ... })(i)."
    ),
    "global_var_thread": (
        "Bảo vệ biến global bằng threading.Lock(). "
        "Dùng with lock: trước mọi read/write trong thread function."
    ),
    "shared_list_no_lock": (
        "Thay list thường bằng queue.Queue() cho producer-consumer pattern, "
        "hoặc bọc mọi append/read bằng threading.Lock()."
    ),
    "thread_read_write_race": (
        "Dùng threading.RLock() để bảo vệ cả read và write. "
        "Tránh iterate collection trong khi thread khác modify."
    ),
    "missing_join": (
        "Gọi thread.join() trước khi đọc kết quả từ thread. "
        "Hoặc dùng concurrent.futures.ThreadPoolExecutor để lấy result an toàn."
    ),
    "singleton_lazy_init": (
        "Dùng threading.Lock() để bảo vệ lazy initialization: "
        "with lock: if instance is None: instance = ... "
        "Hoặc dùng module-level singleton (Python import là thread-safe)."
    ),
    "counter_no_atomic": (
        "JS: Tránh count++ trong async callback với shared variable — "
        "dùng single Promise chain hoặc Atomics nếu dùng SharedArrayBuffer. "
        "Python: Dùng threading.Lock() hoặc concurrent.futures để serialize increment."
    ),
    "unhandled_rejection": (
        "Thêm .catch(err => ...) sau .then(), hoặc bọc toàn bộ trong try/catch nếu dùng async/await. "
        "Node.js sẽ crash process nếu unhandledRejection không được handle."
    ),
    "double_callback": (
        "Thêm return trước mỗi cb() call để đảm bảo chỉ gọi một lần: "
        "if (err) return cb(err); — thiếu return khiến callback bị fired nhiều lần."
    ),
    "zalgo": (
        "Đảm bảo callback luôn được gọi async: bọc sync path bằng process.nextTick(() => cb(result)) "
        "để hành vi nhất quán bất kể cache hit hay miss."
    ),
    "context_loss_this": (
        "Thay function() bằng arrow function để giữ this từ outer scope: "
        "setTimeout(() => { console.log(this.name); }, 100) "
        "Hoặc dùng const self = this trước setTimeout rồi dùng self trong callback."
    ),
    "callback_hell": (
        "Refactor sang async/await: thay nested callbacks bằng các await statement tuần tự. "
        "Hoặc tách mỗi callback thành named function riêng để flatten pyramid."
    ),
    "resource_exhaustion": (
        "Giới hạn concurrency bằng p-limit: const limit = pLimit(10); "
        "await Promise.all(items.map(item => limit(() => process(item)))) "
        "Hoặc chunk array và xử lý từng batch."
    ),
    "sequential_awaits": (
        "Chạy song song bằng Promise.all(): "
        "const [user, stats, friends] = await Promise.all([getUser(id), getStats(id), getFriends(id)]) "
        "Chỉ dùng await tuần tự khi call sau phụ thuộc kết quả call trước."
    ),
    "buffer_leak": (
        "Thêm error handler cho stream trước khi pipe: "
        "readStream.on('error', err => { writeStream.destroy(); next(err); }).pipe(writeStream) "
        "Hoặc dùng pipeline() từ stream/promises để tự động cleanup khi lỗi."
    ),
    "sync_io_blocking": (
        "Thay hàm *Sync bằng bản Promise/callback tương ứng, dùng await: "
        "const fs = require('fs').promises; const data = await fs.readFile(path, 'utf8') "
        "Sync I/O block toàn bộ event loop, khiến mọi request khác phải chờ."
    ),
}

# Severity mặc định cho mỗi pattern
_SEVERITY_MAP: dict[str, str] = {
    "shared_var_settimeout": "medium",
    "promise_no_await": "low",
    "concurrent_write_array": "high",
    "closure_loop_var": "medium",
    "global_var_thread": "high",
    "shared_list_no_lock": "high",
    "thread_read_write_race": "high",
    "missing_join": "high",
    "singleton_lazy_init": "medium",
    "counter_no_atomic": "medium",
    "unhandled_rejection": "medium",
    "double_callback": "high",
    "zalgo": "high",
    "context_loss_this": "medium",
    "callback_hell": "low",
    "resource_exhaustion": "high",
    "sequential_awaits": "medium",
    "buffer_leak": "high",
    "sync_io_blocking": "high",
}

_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_line_start(line_range: Any) -> int:
    """
    Lấy số dòng đầu từ line_range để sort.
    Chấp nhận: "12-18", "42", [12, 18], 42
    """
    if isinstance(line_range, list):
        return int(line_range[0]) if line_range else 0
    if isinstance(line_range, int):
        return line_range
    # string: "12-18" hoặc "42"
    try:
        return int(str(line_range).split("-")[0].strip())
    except (ValueError, AttributeError):
        return 0


def _normalize_line_range(line_range: Any) -> str:
    """Chuẩn hóa line_range về string format "start-end" hoặc "line"."""
    if isinstance(line_range, list) and len(line_range) == 2:
        return f"{line_range[0]}-{line_range[1]}"
    if isinstance(line_range, list) and len(line_range) == 1:
        return str(line_range[0])
    return str(line_range)


_MAX_SNIPPET_LINES = 12


def _extract_snippet(code: str, line_range: str) -> str | None:
    """
    Trích đoạn code gốc tại line_range (1-based, inclusive) để hiển thị inline
    trong issue card mà không cần người dùng tự đếm dòng trong editor.

    "12-18" -> lines[11:18], "42" -> lines[41:42], "all" -> None (không snippet cụ thể).
    Giới hạn _MAX_SNIPPET_LINES để tránh dán nguyên cả file vào 1 issue.
    """
    if not code or line_range == "all":
        return None

    lines = code.splitlines()
    try:
        parts = line_range.split("-")
        start = int(parts[0].strip())
        end = int(parts[1].strip()) if len(parts) > 1 else start
    except (ValueError, IndexError):
        return None

    start = max(1, start)
    end = min(len(lines), end)
    if start > end or start > len(lines):
        return None

    if end - start + 1 > _MAX_SNIPPET_LINES:
        end = start + _MAX_SNIPPET_LINES - 1

    return "\n".join(lines[start - 1:end])


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def format_report(raw_detections: list[dict], code: str = "") -> list[Issue]:
    """
    Format raw detections từ race_detector.py thành List[Issue].

    Args:
        raw_detections: list[dict] từ race_detector.detectRaceConditions()
            Mỗi dict cần có:
                pattern_id  — str, khớp với _FIX_TEMPLATES key
                line_range  — str/list/int, dòng liên quan
                description — str, mô tả chi tiết từ detector
            Tùy chọn:
                severity    — str, override mặc định từ _SEVERITY_MAP
        code: source code gốc, dùng để trích code_snippet tại line_range.
            Optional để giữ backward-compat với các nơi gọi cũ không cần snippet.

    Returns:
        List[Issue] sorted: high → medium → low, rồi theo line_range tăng dần.
        Empty list nếu raw_detections rỗng.

    Ví dụ input:
        [
            {
                "pattern_id": "closure_loop_var",
                "line_range": [12, 18],
                "description": "var i trong for-loop bị capture bởi setTimeout callback"
            }
        ]
    """
    if not raw_detections:
        return []

    issues: list[Issue] = []

    for det in raw_detections:
        pattern_id = det.get("pattern_id", "")
        line_range = _normalize_line_range(det.get("line_range", "0"))
        description = det.get("description", "Race condition detected.")

        # Severity: dùng override từ detector nếu có, không thì dùng map, fallback medium
        severity = det.get("severity") or _SEVERITY_MAP.get(pattern_id, "medium")
        if severity not in ("high", "medium", "low"):
            severity = "medium"

        # Fix: lấy từ template, fallback generic nếu pattern_id lạ
        fix = _FIX_TEMPLATES.get(
            pattern_id,
            "Xem xét cơ chế đồng bộ hóa phù hợp (Lock, Queue, async/await, Promise chain).",
        )

        issues.append(Issue(
            line_range=line_range,
            severity=severity,      # type: ignore[arg-type]
            description=description,
            fix=fix,
            pattern_id=pattern_id or "unknown",
            code_snippet=_extract_snippet(code, line_range),
        ))

    # Sort: severity trước, line_range sau
    issues.sort(key=lambda i: (
        _SEVERITY_ORDER.get(i.severity, 99),
        _parse_line_start(i.line_range),
    ))

    return issues
