"""
dataset_validator.py — ThreadLearn Dataset Reviewer (AI1-01)
=====================================================
Tool kiểm tra chất lượng dataset JS concurrent cho fine-tuning Qwen2.5-Coder-1.5B.

Các kiểm tra được thực hiện:
  [A] Cấu trúc JSON & Encoding
  [B] Cú pháp JS (esprima)
  [C] Độ dài code (< 200 dòng)
  [D] Từ khóa concurrent trong output
  [E] Template literal bug (single-quote dùng thay backtick)
  [F] Duplicate URL pattern trong cùng 1 mẫu
  [G] Semantic consistency (tên function đầu vào ≠ rỗng)
  [H] Phân bố category (balance report)
  [I] Kiểm tra pattern chuyển đổi đúng theo category

Xuất báo cáo: dataset_review_report.txt
"""

import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime

try:
    import esprima
    ESPRIMA_AVAILABLE = True
except ImportError:
    ESPRIMA_AVAILABLE = False
    print("⚠️  Cảnh báo: Module 'esprima' chưa được cài. Bỏ qua kiểm tra cú pháp JS.")
    print("   Cài đặt: pip install esprima\n")


# ─────────────────────────────────────────────
#  CẤU HÌNH
# ─────────────────────────────────────────────

DATASET_FILES = ["my_dataset.json", "raw_dataset.json"]
REPORT_FILE   = "dataset_review_report.txt"
MAX_LINES     = 200

# Từ khóa concurrent bắt buộc xuất hiện trong OUTPUT
CONCURRENT_KEYWORDS = [
    "async", "await", "Promise", "Worker", "cluster",
    "ReadableStream", "generator", "yield", "setTimeout",
    "setInterval", "EventEmitter",
]

# Tỉ lệ tối đa 1 category được chiếm (cảnh báo nếu vượt)
MAX_CATEGORY_RATIO = 0.20   # 20%
MIN_CATEGORY_PAIRS = 15     # Tối thiểu cặp/category để học được

# Category → pattern phải có trong OUTPUT để coi là đúng transformation
CATEGORY_OUTPUT_PATTERNS = {
    "sequential_await_to_parallel":   [r"Promise\.all\s*\("],
    "concurrency_limit":              [r"Promise\.race\s*\(", r"executing", r"semaphore", r"limit", r"batch"],
    "sequential_loop_to_parallel":    [r"Promise\.all\s*\(", r"\.map\s*\("],
    "callback_to_async":              [r"\basync\b", r"\bawait\b", r"new Promise"],
    "race_condition_fix":             [r"#queue|#lock|mutex|Mutex|SafeCounter|\.then\s*\(async"],
    "error_handling":                 [r"Promise\.allSettled\s*\(", r"try\s*{", r"catch\s*\("],
    "streaming":                      [r"ReadableStream|getReader|async\s+function\s*\*|yield"],
    "debounce":                       [r"debounce|clearTimeout|setTimeout"],
    "pagination_parallel":            [r"Promise\.all\s*\(", r"batch|page"],
    "read_transform_write_parallel":  [r"Promise\.all\s*\(", r"batch|chunk"],
    "worker_threads":                 [r"require\s*\(\s*['\"]worker_threads['\"]|new Worker"],
    "chain_to_async":                 [r"\basync\b", r"\bawait\b"],
    "sync_to_async":                  [r"\basync\b", r"\bawait\b"],
    "jquery_to_fetch":                [r"\bfetch\s*\("],
    "event_to_promise":               [r"new Promise", r"resolve\s*\("],
    "polling_to_generator":           [r"async\s+function\s*\*|yield|for\s+await"],
    "xhr_to_fetch":                   [r"\bfetch\s*\("],
    "fs_callback_to_async":           [r"fs\.promises|await\s+fs", r"\basync\b"],
    "http_callback_to_async":         [r"\bfetch\s*\(", r"\basync\b"],
    "callback_to_promise":            [r"new Promise", r"\basync\b"],
    "io_bound":                       [r"\basync\b", r"\bawait\b"],
    "cpu_bound":                      [r"Worker|worker_threads|cluster"],
    "file_io":                        [r"fs\.promises|createReadStream|\basync\b"],
}

# Category input KHÔNG được chứa Promise.all (chứng tỏ chưa convert)
CATEGORY_INPUT_ANTI_PATTERNS = {
    "sequential_await_to_parallel": [r"Promise\.all\s*\("],
    "sequential_loop_to_parallel":  [r"Promise\.all\s*\("],
}


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def check_js_syntax(js_code: str):
    """Parse JS code bằng esprima. Trả về (valid: bool, error: str | None)."""
    if not ESPRIMA_AVAILABLE:
        return None, "esprima không khả dụng"
    try:
        esprima.parseScript(js_code, {"tolerant": True})
        return True, None
    except Exception as e:
        return False, str(e)[:120]


def detect_template_literal_bug(code: str):
    """
    Phát hiện bug: dùng single/double quote chứa ${...} thay vì backtick.
    Ví dụ: '/api/users/${userId}' — interpolation KHÔNG hoạt động.
    """
    pattern = re.compile(r"""['"][^'"]*\$\{[^}]+\}[^'"]*['"]""")
    matches = pattern.findall(code)
    return matches


def detect_duplicate_url_fetch(code: str):
    """
    Phát hiện fetch() gọi cùng 1 URL nhiều lần trong cùng 1 đoạn code.
    Dấu hiệu generated template kém chất lượng.
    """
    url_pattern = re.compile(r"fetch\s*\(\s*([`'\"][^`'\"]+[`'\"])")
    urls = url_pattern.findall(code)
    if len(urls) < 2:
        return []
    counter = Counter(urls)
    return [url for url, count in counter.items() if count > 1]


def check_category_transformation(category: str, input_code: str, output_code: str):
    """
    Kiểm tra output có chứa pattern đúng cho category không.
    Trả về list các pattern bị thiếu.
    """
    issues = []

    # Kiểm tra OUTPUT phải có pattern
    expected_patterns = CATEGORY_OUTPUT_PATTERNS.get(category, [])
    if expected_patterns:
        found_any = any(re.search(p, output_code) for p in expected_patterns)
        if not found_any:
            issues.append(
                f"Output không có pattern đúng cho '{category}' "
                f"(cần một trong: {', '.join(expected_patterns[:3])})"
            )

    # Kiểm tra INPUT không được đã có pattern của output (đã được convert rồi)
    anti_patterns = CATEGORY_INPUT_ANTI_PATTERNS.get(category, [])
    for ap in anti_patterns:
        if re.search(ap, input_code):
            issues.append(
                f"Input đã chứa pattern '{ap}' — cặp này có thể bị lỗi (input đã convert rồi?)"
            )

    return issues


def count_lines(code: str) -> int:
    return len(code.splitlines())


def check_es_private_fields(code: str) -> bool:
    """Phát hiện cú pháp private class fields (#field) — ES2022+."""
    return bool(re.search(r"#\w+", code))


def check_web_streams_api(code: str) -> bool:
    """Phát hiện Web Streams API — chỉ hoạt động Node.js >= 18."""
    return bool(re.search(r"getReader\s*\(\)|ReadableStream", code))


# ─────────────────────────────────────────────
#  ANALYZER CHÍNH
# ─────────────────────────────────────────────

def analyze_dataset(file_path: str):
    """
    Phân tích toàn bộ dataset và trả về dict kết quả chi tiết.
    """
    result = {
        "file": file_path,
        "status": "ok",
        "total": 0,
        "valid": 0,
        "errors_by_type": defaultdict(int),
        "samples": [],          # danh sách từng mẫu
        "category_dist": Counter(),
        "global_warnings": [],
    }

    if not os.path.exists(file_path):
        result["status"] = "file_not_found"
        return result

    # ── A. Đọc file ─────────────────────────────
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except UnicodeDecodeError:
        result["status"] = "encoding_error"
        return result
    except json.JSONDecodeError as e:
        result["status"] = f"json_error: {e}"
        return result

    if not isinstance(data, list):
        result["status"] = "not_a_list"
        return result

    result["total"] = len(data)

    # ── Per-sample checks ────────────────────────
    for idx, item in enumerate(data, 1):
        sample = {
            "idx": idx,
            "category": item.get("category", "unknown"),
            "errors": [],
            "warnings": [],
            "valid": False,
        }

        # B. Field check
        for field in ["input", "output"]:
            if field not in item:
                sample["errors"].append(f"[STRUCT] Thiếu trường '{field}'")

        if any("[STRUCT]" in e for e in sample["errors"]):
            result["samples"].append(sample)
            result["errors_by_type"]["missing_field"] += 1
            continue

        inp = item["input"]
        out = item["output"]
        cat = item.get("category", "unknown")
        result["category_dist"][cat] += 1

        # C. Độ dài
        inp_lines = count_lines(inp)
        out_lines = count_lines(out)
        if inp_lines > MAX_LINES:
            sample["errors"].append(f"[LENGTH] Input quá dài: {inp_lines} dòng (max {MAX_LINES})")
            result["errors_by_type"]["too_long"] += 1
        if out_lines > MAX_LINES:
            sample["errors"].append(f"[LENGTH] Output quá dài: {out_lines} dòng (max {MAX_LINES})")
            result["errors_by_type"]["too_long"] += 1

        # D. Cú pháp JS
        valid_inp, err_inp = check_js_syntax(inp)
        valid_out, err_out = check_js_syntax(out)
        if valid_inp is False:
            sample["errors"].append(f"[SYNTAX] Input lỗi cú pháp: {err_inp}")
            result["errors_by_type"]["syntax_error"] += 1
        if valid_out is False:
            sample["errors"].append(f"[SYNTAX] Output lỗi cú pháp: {err_out}")
            result["errors_by_type"]["syntax_error"] += 1

        # E. Từ khóa concurrent
        has_kw = any(kw in out for kw in CONCURRENT_KEYWORDS)
        if not has_kw:
            sample["warnings"].append(
                "[KW] Output không chứa từ khóa concurrent nào (async/await/Promise...)"
            )
            result["errors_by_type"]["missing_concurrent_kw"] += 1

        # F. Template literal bug
        tl_bugs_inp = detect_template_literal_bug(inp)
        tl_bugs_out = detect_template_literal_bug(out)
        if tl_bugs_inp:
            sample["errors"].append(
                f"[TEMPLATE_BUG] Input dùng quote thay backtick: {tl_bugs_inp[:2]}"
            )
            result["errors_by_type"]["template_literal_bug"] += 1
        if tl_bugs_out:
            sample["errors"].append(
                f"[TEMPLATE_BUG] Output dùng quote thay backtick: {tl_bugs_out[:2]}"
            )
            result["errors_by_type"]["template_literal_bug"] += 1

        # G. Duplicate URL fetch
        dup_urls_inp = detect_duplicate_url_fetch(inp)
        dup_urls_out = detect_duplicate_url_fetch(out)
        if dup_urls_inp:
            sample["warnings"].append(
                f"[DUP_URL] Input fetch cùng URL nhiều lần: {dup_urls_inp[:2]}"
            )
        if dup_urls_out:
            sample["warnings"].append(
                f"[DUP_URL] Output fetch cùng URL nhiều lần: {dup_urls_out[:2]}"
            )
        if dup_urls_inp or dup_urls_out:
            result["errors_by_type"]["duplicate_url_fetch"] += 1

        # H. Category transformation pattern check
        trans_issues = check_category_transformation(cat, inp, out)
        for issue in trans_issues:
            sample["errors"].append(f"[TRANSFORM] {issue}")
        if trans_issues:
            result["errors_by_type"]["wrong_transformation"] += 1

        # I. ES version warnings
        if check_es_private_fields(out):
            sample["warnings"].append(
                "[ES_VER] Dùng Private Class Fields (#field) — yêu cầu ES2022 / Node.js >= 12"
            )
        if check_web_streams_api(out):
            sample["warnings"].append(
                "[COMPAT] Dùng Web Streams API (getReader) — yêu cầu Node.js >= 18"
            )

        # Kết luận mẫu
        sample["valid"] = len(sample["errors"]) == 0
        if sample["valid"]:
            result["valid"] += 1

        result["samples"].append(sample)

    # ── Global: phân bố category ────────────────
    total = result["total"]
    for cat, count in result["category_dist"].items():
        ratio = count / total if total > 0 else 0
        if ratio > MAX_CATEGORY_RATIO:
            result["global_warnings"].append(
                f"[BALANCE] Category '{cat}' chiếm {ratio*100:.1f}% ({count}/{total}) "
                f"— vượt ngưỡng {MAX_CATEGORY_RATIO*100:.0f}%, nguy cơ overfit"
            )
        if count < MIN_CATEGORY_PAIRS:
            result["global_warnings"].append(
                f"[BALANCE] Category '{cat}' chỉ có {count} cặp "
                f"— dưới ngưỡng tối thiểu {MIN_CATEGORY_PAIRS}, model khó học được"
            )

    return result


# ─────────────────────────────────────────────
#  BÁO CÁO
# ─────────────────────────────────────────────

SEVERITY_ICON = {
    "errors":   "❌",
    "warnings": "⚠️ ",
}

def build_report(all_results: list) -> str:
    lines = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines += [
        "=" * 70,
        "   THREADLEARN — BÁO CÁO KIỂM TRA DATASET AI1-01",
        f"   Thời gian: {ts}",
        "=" * 70,
        "",
    ]

    grand_total = grand_valid = grand_fail = 0
    grand_errors_by_type = defaultdict(int)

    for res in all_results:
        fname = res["file"]

        lines.append(f"{'─'*70}")
        lines.append(f"📁 FILE: {fname}")
        lines.append(f"{'─'*70}")

        if res["status"] != "ok":
            lines.append(f"  ❌ KHÔNG THỂ ĐỌC FILE — Lý do: {res['status']}")
            lines.append("")
            continue

        total  = res["total"]
        valid  = res["valid"]
        fail   = total - valid
        grand_total += total
        grand_valid += valid
        grand_fail  += fail

        lines.append(f"  📊 Tổng mẫu  : {total}")
        lines.append(f"  ✅ Đạt chuẩn : {valid}  ({valid/total*100:.1f}%)")
        lines.append(f"  ❌ Có lỗi    : {fail}   ({fail/total*100:.1f}%)")
        lines.append("")

        # Thống kê lỗi theo loại
        lines.append("  📌 THỐNG KÊ LỖI THEO LOẠI:")
        if res["errors_by_type"]:
            for etype, count in sorted(res["errors_by_type"].items(), key=lambda x: -x[1]):
                grand_errors_by_type[etype] += count
                lines.append(f"     • {etype:<30s}: {count} mẫu")
        else:
            lines.append("     (Không có lỗi nào!)")
        lines.append("")

        # Chi tiết từng mẫu có lỗi
        bad_samples = [s for s in res["samples"] if not s["valid"] or s["warnings"]]
        if bad_samples:
            lines.append(f"  📋 CHI TIẾT MẪU CÓ VẤN ĐỀ ({len(bad_samples)} mẫu):")
            for s in bad_samples:
                icon = "❌" if not s["valid"] else "⚠️ "
                lines.append(f"    {icon} Mẫu #{s['idx']}  [category: {s['category']}]")
                for err in s["errors"]:
                    lines.append(f"         ❌ {err}")
                for warn in s["warnings"]:
                    lines.append(f"         ⚠️  {warn}")
        else:
            lines.append("  🎉 Không có mẫu nào có vấn đề!")
        lines.append("")

        # Phân bố category
        lines.append("  📊 PHÂN BỐ CATEGORY:")
        sorted_cats = sorted(res["category_dist"].items(), key=lambda x: -x[1])
        for cat, count in sorted_cats:
            ratio = count / total * 100
            bar   = "█" * int(ratio / 2)
            flag  = " ⚠️ OVERFIT RISK"  if count / total > MAX_CATEGORY_RATIO else (
                    " 🔴 QUÁ ÍT"       if count < MIN_CATEGORY_PAIRS else "")
            lines.append(f"     {cat:<38s} {count:>4d} ({ratio:5.1f}%) {bar}{flag}")
        lines.append("")

        # Cảnh báo toàn cục
        if res["global_warnings"]:
            lines.append(f"  🌐 CẢNH BÁO TỔNG QUAN ({len(res['global_warnings'])} mục):")
            for gw in res["global_warnings"]:
                lines.append(f"     {gw}")
        lines.append("")

    # ── TỔNG KẾT TOÀN BỘ ──────────────────────────
    lines.append("=" * 70)
    lines.append("   TỔNG KẾT TOÀN BỘ DATASET")
    lines.append("=" * 70)
    lines.append(f"  Tổng mẫu      : {grand_total}")
    if grand_total > 0:
        lines.append(f"  Đạt chuẩn     : {grand_valid}  ({grand_valid/grand_total*100:.1f}%)")
        lines.append(f"  Có lỗi        : {grand_fail}   ({grand_fail/grand_total*100:.1f}%)")
    lines.append("")

    if grand_errors_by_type:
        lines.append("  Top lỗi phổ biến nhất:")
        for etype, cnt in sorted(grand_errors_by_type.items(), key=lambda x: -x[1])[:8]:
            lines.append(f"     • {etype:<35s}: {cnt}")
    lines.append("")

    # Điểm chất lượng ước tính
    if grand_total > 0:
        score = _estimate_quality_score(grand_valid, grand_total, grand_errors_by_type)
        lines.append(f"  📈 ĐIỂM CHẤT LƯỢNG ƯỚC TÍNH: {score}/10")
        lines.append(f"  {'✅ Có thể fine-tune!' if score >= 7 else '⚠️  Nên fix lỗi trước khi fine-tune.'}")
    lines.append("")

    # Đề xuất hành động
    lines.append("─" * 70)
    lines.append("  📋 ĐỀ XUẤT HÀNH ĐỘNG (theo thứ tự ưu tiên):")
    lines.append("")
    _add_recommendations(lines, grand_errors_by_type, all_results)

    lines.append("")
    lines.append("=" * 70)
    lines.append("   Kết thúc báo cáo — ThreadLearn Dataset Review Tool")
    lines.append("=" * 70)

    return "\n".join(lines)


def _estimate_quality_score(valid: int, total: int, errors_by_type: dict) -> float:
    """Ước tính điểm chất lượng 0–10 dựa trên tỉ lệ mẫu hợp lệ và phân bố lỗi."""
    if total == 0:
        return 0.0
    base = (valid / total) * 10

    # Trừ điểm theo lỗi nghiêm trọng
    deductions = 0
    if errors_by_type.get("template_literal_bug", 0) > 5:
        deductions += 1.0
    if errors_by_type.get("duplicate_url_fetch", 0) > 10:
        deductions += 0.5
    if errors_by_type.get("syntax_error", 0) > 5:
        deductions += 1.5
    if errors_by_type.get("wrong_transformation", 0) > 10:
        deductions += 1.0

    score = max(0.0, min(10.0, base - deductions))
    return round(score, 1)


def _add_recommendations(lines: list, errors_by_type: dict, all_results: list):
    recs = []

    if errors_by_type.get("template_literal_bug", 0) > 0:
        recs.append((
            "P0 🔴",
            "Fix Template Literal Bug",
            f"  {errors_by_type['template_literal_bug']} mẫu dùng single/double quote chứa ${{...}}\n"
            "       → Thay tất cả '...${{...}}...' bằng backtick `...${{...}}...`"
        ))

    if errors_by_type.get("duplicate_url_fetch", 0) > 0:
        recs.append((
            "P0 🔴",
            "Loại bỏ Duplicate URL Fetch",
            f"  {errors_by_type['duplicate_url_fetch']} mẫu fetch cùng 1 URL nhiều lần — phi thực tế\n"
            "       → Regenerate với endpoint khác nhau (/profile, /orders, /messages)"
        ))

    if errors_by_type.get("syntax_error", 0) > 0:
        recs.append((
            "P0 🔴",
            "Fix Lỗi Cú Pháp JS",
            f"  {errors_by_type['syntax_error']} mẫu có lỗi parse — không thể dùng để train\n"
            "       → Review và sửa từng mẫu bị lỗi cú pháp"
        ))

    if errors_by_type.get("wrong_transformation", 0) > 0:
        recs.append((
            "P1 🟡",
            "Fix Sai Pattern Transformation",
            f"  {errors_by_type['wrong_transformation']} mẫu output không đúng pattern category\n"
            "       → Kiểm tra lại mapping category → pattern output"
        ))

    # Check long-tail categories
    all_cats = Counter()
    all_totals = 0
    for res in all_results:
        if res["status"] == "ok":
            all_cats.update(res["category_dist"])
            all_totals += res["total"]

    low_cats = [cat for cat, cnt in all_cats.items() if cnt < MIN_CATEGORY_PAIRS]
    if low_cats:
        recs.append((
            "P1 🟡",
            "Bổ sung Long-tail Categories",
            f"  {len(low_cats)} category có < {MIN_CATEGORY_PAIRS} cặp: {', '.join(low_cats[:5])}\n"
            f"       → Sinh thêm để mỗi category đạt tối thiểu {MIN_CATEGORY_PAIRS} cặp"
        ))

    # Check overfit risk
    for cat, cnt in all_cats.items():
        if all_totals > 0 and cnt / all_totals > MAX_CATEGORY_RATIO:
            recs.append((
                "P1 🟡",
                f"Giảm '{cat}' ({cnt} cặp, {cnt/all_totals*100:.0f}%)",
                f"  Vượt ngưỡng {MAX_CATEGORY_RATIO*100:.0f}% — nguy cơ model overfit vào pattern này\n"
                "       → Giữ lại ~80–100 cặp có structure đa dạng nhất, loại duplicate"
            ))

    recs.append((
        "P2 🔵",
        "Thêm Missing Patterns",
        "  Các pattern quan trọng chưa có:\n"
        "       → AbortController + fetch cancellation\n"
        "       → for await...of với async iterators\n"
        "       → Promise.any (racing multiple endpoints)\n"
        "       → Mutex / Lock pattern"
    ))

    recs.append((
        "P3 ⚪",
        "Ghi chú ES Version",
        "  Một số mẫu dùng ES2022+ (private fields) hoặc Node.js >= 18 (Web Streams)\n"
        "       → Thêm comment '// Node.js >= 18' hoặc chuẩn hóa về ES2020"
    ))

    for priority, title, desc in recs:
        lines.append(f"  [{priority}] {title}")
        lines.append(f"       {desc}")
        lines.append("")


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    print("\n" + "=" * 70)
    print("   🚀 THREADLEARN — DATASET REVIEWER AI1-01")
    print("=" * 70)
    print(f"   Kiểm tra {len(DATASET_FILES)} file: {', '.join(DATASET_FILES)}")
    print(f"   Báo cáo sẽ được lưu vào: {REPORT_FILE}")
    print("=" * 70 + "\n")

    all_results = []
    for fpath in DATASET_FILES:
        print(f"🔍 Đang phân tích: {fpath} ...")
        res = analyze_dataset(fpath)
        all_results.append(res)

        if res["status"] != "ok":
            print(f"   ❌ Lỗi: {res['status']}\n")
        else:
            total = res["total"]
            valid = res["valid"]
            print(f"   ✅ Hoàn thành: {valid}/{total} mẫu đạt chuẩn "
                  f"({valid/total*100:.1f}%)\n")

    # Sinh báo cáo
    report_text = build_report(all_results)

    # In ra console
    print("\n" + report_text)

    # Ghi file
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"\n✅ Đã lưu báo cáo đầy đủ vào: {REPORT_FILE}")


if __name__ == "__main__":
    main()