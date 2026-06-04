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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def format_report(raw_detections: list[dict]) -> list[Issue]:
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
        ))

    # Sort: severity trước, line_range sau
    issues.sort(key=lambda i: (
        _SEVERITY_ORDER.get(i.severity, 99),
        _parse_line_start(i.line_range),
    ))

    return issues
