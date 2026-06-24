"""
AI2-04: Tests for report_formatter.py.
Chạy: pytest ai2/tests/test_report_formatter.py -v
"""

import pytest
from report_formatter import format_report


# ---------------------------------------------------------------------------
# Basic output
# ---------------------------------------------------------------------------

def test_empty_input_returns_empty():
    assert format_report([]) == []


def test_single_detection_returns_one_issue():
    raw = [{
        "pattern_id": "closure_loop_var",
        "line_range": "12-18",
        "description": "var i bị capture bởi setTimeout callback",
    }]
    issues = format_report(raw)
    assert len(issues) == 1
    assert issues[0].severity == "medium"
    assert "let" in issues[0].fix


def test_fix_template_applied_by_pattern_id():
    raw = [{"pattern_id": "global_var_thread", "line_range": "5", "description": "x"}]
    issues = format_report(raw)
    assert "threading.Lock" in issues[0].fix


def test_unknown_pattern_id_gets_generic_fix():
    raw = [{"pattern_id": "some_unknown_pattern", "line_range": "1", "description": "x"}]
    issues = format_report(raw)
    assert len(issues) == 1
    assert issues[0].severity == "medium"   # fallback
    # fix không rỗng
    assert len(issues[0].fix) > 0


# ---------------------------------------------------------------------------
# Severity
# ---------------------------------------------------------------------------

def test_severity_from_severity_map():
    """concurrent_write_array → high theo _SEVERITY_MAP."""
    raw = [{"pattern_id": "concurrent_write_array", "line_range": "1", "description": "x"}]
    issues = format_report(raw)
    assert issues[0].severity == "high"


def test_severity_override_from_detector():
    """detector có thể override severity."""
    raw = [{
        "pattern_id": "closure_loop_var",   # map default = medium
        "line_range": "1",
        "description": "x",
        "severity": "high",   # detector override
    }]
    issues = format_report(raw)
    assert issues[0].severity == "high"


def test_invalid_severity_falls_back_to_medium():
    raw = [{"pattern_id": "closure_loop_var", "line_range": "1", "description": "x", "severity": "critical"}]
    issues = format_report(raw)
    assert issues[0].severity == "medium"


# ---------------------------------------------------------------------------
# Sort order
# ---------------------------------------------------------------------------

def test_sorted_high_before_medium_before_low():
    raw = [
        {"pattern_id": "promise_no_await", "line_range": "1", "description": "low sev"},   # low
        {"pattern_id": "global_var_thread", "line_range": "5", "description": "high sev"}, # high
        {"pattern_id": "closure_loop_var", "line_range": "3", "description": "med sev"},   # medium
    ]
    issues = format_report(raw)
    severities = [i.severity for i in issues]
    assert severities == ["high", "medium", "low"]


def test_same_severity_sorted_by_line_ascending():
    raw = [
        {"pattern_id": "global_var_thread", "line_range": "20", "description": "high at 20"},
        {"pattern_id": "missing_join", "line_range": "5", "description": "high at 5"},
        {"pattern_id": "shared_list_no_lock", "line_range": "12", "description": "high at 12"},
    ]
    issues = format_report(raw)
    line_starts = [int(i.line_range.split("-")[0]) for i in issues]
    assert line_starts == sorted(line_starts)


# ---------------------------------------------------------------------------
# line_range normalization
# ---------------------------------------------------------------------------

def test_line_range_list_normalized_to_string():
    raw = [{"pattern_id": "closure_loop_var", "line_range": [10, 15], "description": "x"}]
    issues = format_report(raw)
    assert issues[0].line_range == "10-15"


def test_line_range_int_normalized_to_string():
    raw = [{"pattern_id": "closure_loop_var", "line_range": 42, "description": "x"}]
    issues = format_report(raw)
    assert issues[0].line_range == "42"


def test_line_range_string_kept():
    raw = [{"pattern_id": "closure_loop_var", "line_range": "7-9", "description": "x"}]
    issues = format_report(raw)
    assert issues[0].line_range == "7-9"


# ---------------------------------------------------------------------------
# All 10 pattern IDs có fix template
# ---------------------------------------------------------------------------

ALL_PATTERNS = [
    "shared_var_settimeout",
    "promise_no_await",
    "concurrent_write_array",
    "closure_loop_var",
    "global_var_thread",
    "shared_list_no_lock",
    "thread_read_write_race",
    "missing_join",
    "singleton_lazy_init",
    "counter_no_atomic",
]

@pytest.mark.parametrize("pattern_id", ALL_PATTERNS)
def test_all_patterns_have_fix_template(pattern_id):
    raw = [{"pattern_id": pattern_id, "line_range": "1", "description": "test"}]
    issues = format_report(raw)
    assert len(issues) == 1
    assert len(issues[0].fix) > 20   # fix không phải generic ngắn
