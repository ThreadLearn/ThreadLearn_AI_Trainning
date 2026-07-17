"""
AI2-05/06: RAG Pipeline
Flow: code → keyword extraction → BM25 top-3 docs → build prompt → LLM → List[Issue]

Keyword extraction dùng ast_preprocessor.extract_keywords() (AST-based, esprima).
Fallback sang bm25_module.tokenize() nếu import fail.
"""

import os
import re
import sys
from typing import Callable, List, TYPE_CHECKING

from bm25_module import tokenize
from schemas import Issue, DocUsed
import llm_client
from race_detector import detectRaceConditions, count_patterns_checked
from report_formatter import format_report
from output_parser import cleanOutput

if TYPE_CHECKING:
    from bm25_module import BM25Retriever

# AST-based keyword extraction từ AI1
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "training", "modules"))
    from ast_preprocessor import extract_keywords as _ast_extract_keywords
    _HAS_AST = True
except ImportError:
    _HAS_AST = False


# ---------------------------------------------------------------------------
# Keyword Extraction
# ---------------------------------------------------------------------------

def _extract_keywords(code: str) -> str:
    """
    Trích keyword từ code để làm BM25 query.

    Ưu tiên semantic pattern detection (regex → category keywords) trước,
    fallback sang AST/tokenize. Category keywords khớp trực tiếp với
    title/content trong knowledge_base.json, tốt hơn function names.
    """
    semantic = _semantic_keywords(code)
    if semantic:
        return semantic
    if _HAS_AST:
        kw = _ast_extract_keywords(code, language="javascript")
        if kw.strip():
            return kw
    return " ".join(tokenize(code)[:20])


# Mapping pattern → BM25 query terms khớp với knowledge_base titles
_SEMANTIC_PATTERNS = [
    # Double Callback
    (r"if\s*\(\s*err\s*\)[^r][^e].*?cb\(|callback\(err\)(?!\s*;?\s*return)",
     "double callback called twice return guard"),
    (r"setTimeout[^}]+cb\(|cb\([^)]*\)[^}]*cb\(",
     "double callback timeout clearTimeout once"),
    # Zalgo
    (r"if\s*\(\s*\w+\[", "zalgo synchronous asynchronous consistent nextTick setImmediate"),
    # Sequential Awaits
    (r"await\s+\w[^\n;]+\n\s*(?:const\s+\w+\s*=\s*)?await\s+\w[^\n;]+\n\s*(?:const\s+\w+\s*=\s*)?await",
     "sequential await Promise.all parallel concurrent"),
    # Unhandled Rejection
    (r"async\s+function[^{]*\{(?![\s\S]{0,200}try\s*\{)",
     "unhandled rejection async catch try error"),
    # Event Loop Blocking
    (r"pbkdf2Sync|execSync|readFileSync|writeFileSync",
     "blocking event loop sync worker thread"),
    (r"for\s*\([^)]+\)\s*\{[^}]*heavyTransform|for\s*\([^)]+\)\s*\{[^}]*crypto",
     "blocking event loop worker setImmediate chunk"),
    # Resource Exhaustion / backpressure
    (r"createReadStream[^}]+\.on\s*\(\s*['\"]data",
     "backpressure stream pause resume drain highWaterMark"),
    (r"Promise\.all\s*\(\s*\w+\.map",
     "resource exhaustion concurrency limit p-limit batch chunk"),
    # Stream Leak
    (r"\.pipe\s*\([^)]*\)\.pipe|createReadStream[^}]+pipe",
     "stream pipeline error destroy cleanup leak"),
    # Context Loss
    (r"this\.\w+[^=\n]*function\s*\(|setTimeout\s*\(\s*function",
     "context loss bind arrow this"),
    # Race Condition — file system
    (r"fs\.exists|fs\.access[^(]*F_OK",
     "race condition file system toctou atomic exclusive wx"),
    # Race Condition — shared state
    (r"job\.data\.status\s*=|\.status\s*===\s*['\"]pending",
     "race condition atomic lock transaction update"),
    # Callback Hell
    (r"function\s*\(err[^)]*\)\s*\{[^}]*function\s*\(err[^)]*\)\s*\{[^}]*function\s*\(err",
     "callback hell async await promise flatten"),
]

import re as _re  # already imported above but safe to re-import

def _semantic_keywords(code: str) -> str:
    """Pattern match code → trả về category keywords cho BM25 query."""
    for pattern, keywords in _SEMANTIC_PATTERNS:
        if _re.search(pattern, code, _re.MULTILINE | _re.DOTALL):
            return keywords
    return ""


# ---------------------------------------------------------------------------
# Prompt Builder
# ---------------------------------------------------------------------------

_MAX_ISSUES_WITH_OWN_FIX = 5


def _build_prompt(code: str, docs: list) -> str:
    """
    Ghép code + context docs thành prompt gửi LLM.

    Model chỉ được fine-tune trên format thuần "Convert to concurrent
    JavaScript:\n\n{code}\n" (ai1_02_format_jsonl.py) — không hề thấy
    context RAG lúc train. Nhồi context bằng cú pháp lạ (vd thẻ
    <reference_docs>) khiến input rơi ra ngoài phân phối huấn luyện và
    model có xu hướng chỉ echo lại code gốc thay vì sinh fix.

    Format dưới đây khớp build_prompt_with_context() trong
    eval/scripts/eval_rag_merged.py: context đặt TRƯỚC, phần cuối luôn
    kết bằng đúng câu lệnh training gốc để model nhận diện điểm bắt đầu
    completion.
    """
    context_parts = []
    for i, doc in enumerate(docs, 1):
        context_parts.append(
            f"Tài liệu {i} — {doc.get('title', '')} [{doc.get('category', '')}]:\n"
            f"{doc.get('content', '')}"
        )

    context = "\n\n".join(context_parts)

    if context:
        return (
            f"Dưới đây là các tài liệu tham khảo về concurrent JavaScript:\n\n"
            f"{context}\n\n"
            f"---\n\n"
            f"Convert to concurrent JavaScript:\n\n{code}\n"
        )
    else:
        return f"Convert to concurrent JavaScript:\n\n{code}\n"


_RE_FOR_DECL = re.compile(r'\bfor\s*\(\s*(?:var|let|const)\s+(\w+)')
_RE_IDENTIFIER = re.compile(r'\b([a-zA-Z_$][\w$]*)\b')
_JS_KEYWORDS = {
    "function", "return", "const", "let", "var", "if", "else", "for", "while",
    "console", "log", "new", "this", "await", "async", "true", "false", "null",
    "undefined", "typeof", "in", "of", "break", "continue", "case", "switch",
}


def _widen_snippet_for_context(full_code: str, snippet: str, line_range: str) -> str:
    """
    Một số detector (vd shared_var_settimeout) trả line_range bắt đầu ngay tại
    setTimeout/callback body, bỏ sót dòng `for (var i...)` khai báo biến phía
    trên. Model nhận snippet cụt như vậy không biết biến đến từ đâu, và có xu
    hướng sinh code lặp lại/vô nghĩa thay vì 1 fix sạch.

    Heuristic: nếu snippet dùng 1 identifier mà không có dòng khai báo
    (var/let/const) của nó trong chính snippet, tìm dòng `for (var|let|const
    X ...)` gần nhất PHÍA TRÊN line_range khai báo đúng biến đó, rồi mở rộng
    snippet để bao gồm từ dòng đó trở đi.
    """
    try:
        start = int(line_range.split("-")[0].strip())
    except (ValueError, IndexError):
        return snippet

    declared_in_snippet = set()
    for m in re.finditer(r'\b(?:var|let|const)\s+(\w+)', snippet):
        declared_in_snippet.add(m.group(1))

    used = {
        tok for tok in _RE_IDENTIFIER.findall(snippet)
        if tok not in _JS_KEYWORDS and tok not in declared_in_snippet
    }
    if not used:
        return snippet

    lines = full_code.splitlines()
    # Tìm dòng for-loop gần nhất phía trên start khai báo 1 trong các biến "used".
    for i in range(min(start, len(lines)) - 1, 0, -1):
        m = _RE_FOR_DECL.search(lines[i - 1])
        if m and m.group(1) in used:
            widened = "\n".join(lines[i - 1:min(start + _MAX_SNIPPET_LINES, len(lines))])
            return widened

    return snippet


_MAX_SNIPPET_LINES = 12


def _generate_fixes_per_issue(
    issues: list[Issue],
    full_code: str,
    raw_docs: list,
    emit: Callable[[str, dict], None] | None = None,
) -> tuple[str, str]:
    """
    Gọi LLM riêng cho từng issue (dùng code_snippet của chính issue đó) thay vì
    1 lần cho toàn file. Lý do: model 1.5B fine-tune không đủ khả năng sửa nhiều
    bug pattern khác nhau cùng lúc trong 1 lần generate — khi file có 2-3 block
    lỗi tương tự (vd: 3 vòng for+var+setTimeout/setInterval), model chỉ sửa
    đúng block đầu tiên và bỏ sót các block còn lại dù cùng pattern.

    Giới hạn số issue được fix riêng bằng _MAX_ISSUES_WITH_OWN_FIX để tránh
    vượt LLM_TIMEOUT_SECONDS khi file có quá nhiều pattern — các issue dư dùng
    lại fix full-file làm fallback (không tốn thêm LLM call).

    Nếu truyền emit (chỉ dùng ở run_streaming), phát 2 loại event sau mỗi
    bước fix xong:
      - "llm_issue_progress": {done, total, current_pattern} — cho checklist
      - "issue_ready": {issue: Issue.model_dump()} — issue đã có fix đầy đủ,
        để FE render ngay IssueCard đó thay vì đợi toàn bộ pipeline xong mới
        thấy 1 lần. Quan trọng khi có nhiều issue (mỗi issue ~15-20s do gọi
        LLM riêng) — người dùng thấy kết quả xuất hiện dần thay vì màn hình
        đứng im rồi "nhảy" toàn bộ ra cùng lúc ở cuối.

    Whole-file fix (1 LLM call cho toàn bộ code) chỉ được gọi LAZY — đúng lúc
    cần dùng lần đầu tiên (issues rỗng, issue thiếu code_snippet, hoặc vượt
    _MAX_ISSUES_WITH_OWN_FIX) — không gọi phủ đầu như trước, vì phần lớn các
    lần phân tích (≤5 issue, đều có snippet riêng) không bao giờ cần đến nó và
    trước đây vẫn tốn ~15-20s gọi vô ích mỗi lần.

    Mutates từng issue.fix trực tiếp. Trả về (full_file_fix, explanation) để
    caller dùng làm fallback issue khi raw_detections rỗng.
    """
    if not issues:
        needs_whole_file = True
        own_fix_count = 0
    else:
        capped = issues[:_MAX_ISSUES_WITH_OWN_FIX]
        own_fix_count = sum(1 for iss in capped if iss.code_snippet and iss.line_range != "all")
        needs_whole_file = (
            len(issues) > _MAX_ISSUES_WITH_OWN_FIX
            or own_fix_count < len(capped)
        )
    total_llm_calls = own_fix_count + (1 if needs_whole_file else 0)
    done_count = 0

    def _report_progress(current_pattern: str | None):
        nonlocal done_count
        done_count += 1
        if emit:
            emit("llm_issue_progress", {
                "done": done_count,
                "total": total_llm_calls,
                "current_pattern": current_pattern,
            })

    def _report_issue_ready(iss: Issue):
        if emit:
            emit("issue_ready", {"issue": iss.model_dump()})

    _full_fix_cache: dict[str, tuple[str, str]] = {}

    def _get_full_file_fix() -> tuple[str, str]:
        """Lazy — gọi LLM cho toàn file chỉ lần đầu cần đến, cache lại cho các
        lần dùng tiếp theo trong cùng 1 request (không gọi lại LLM nhiều lần)."""
        if "value" not in _full_fix_cache:
            full_prompt = _build_prompt(full_code, raw_docs)
            full_llm_output = llm_client.get_llm_fix(full_code, full_prompt)
            full_parsed = cleanOutput(full_llm_output)
            fixed_code = f"```javascript\n{full_parsed['code']}\n```"
            explanation = full_parsed.get(
                "explanation",
                "Phát hiện mã nguồn chưa tối ưu. Hệ thống AI đã cung cấp mã song song hóa an toàn thay thế.",
            )
            _full_fix_cache["value"] = (fixed_code, explanation)
            _report_progress("whole file")
        return _full_fix_cache["value"]

    if not issues:
        fixed_code, explanation = _get_full_file_fix()
        return fixed_code, explanation

    for i, iss in enumerate(issues[:_MAX_ISSUES_WITH_OWN_FIX]):
        snippet = iss.code_snippet
        if not snippet or iss.line_range == "all":
            fixed_code, _ = _get_full_file_fix()
            iss.fix = fixed_code
        else:
            snippet = _widen_snippet_for_context(full_code, snippet, iss.line_range)
            snippet_prompt = _build_prompt(snippet, raw_docs)
            snippet_llm_output = llm_client.get_llm_fix(snippet, snippet_prompt)
            snippet_parsed = cleanOutput(snippet_llm_output)
            iss.fix = f"```javascript\n{snippet_parsed['code']}\n```"
        _report_progress(iss.pattern_id)
        _report_issue_ready(iss)

    if len(issues) > _MAX_ISSUES_WITH_OWN_FIX:
        fixed_code, _ = _get_full_file_fix()
        for iss in issues[_MAX_ISSUES_WITH_OWN_FIX:]:
            iss.fix = fixed_code
            _report_issue_ready(iss)

    # Giá trị trả về ở nhánh này chỉ dùng khi caller thấy issues rỗng — nhưng
    # ta đã return sớm cho case đó ở trên, nên không tới đây. Trả placeholder
    # vô hại (không gọi thêm LLM chỉ để tính giá trị không ai dùng).
    return "", ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run(
    code: str,
    language: str,
    retriever: "BM25Retriever",
) -> tuple[List[Issue], List[DocUsed], int]:
    # 1. RAG
    query = _extract_keywords(code)
    raw_docs = retriever.search(query, top_k=1) if query else []

    # 2. Race Detector (cho descriptions & severity)
    raw_detections = detectRaceConditions(code, language)
    issues = format_report(raw_detections, code)

    # 3. LLM Fix — riêng cho từng issue (xem docstring _generate_fixes_per_issue)
    fallback_fix, fallback_explanation = _generate_fixes_per_issue(issues, code, raw_docs)

    # 4. Fallback issue nếu race detector không tìm thấy pattern nào
    if not issues:
        issues = [Issue(
            line_range="all",
            severity="medium",
            description=fallback_explanation or "Phát hiện mã nguồn chưa tối ưu. Hệ thống AI đã cung cấp mã song song hóa an toàn thay thế.",
            fix=fallback_fix,
        )]

    docs_used = [
        DocUsed(id=doc.get("id", ""), title=doc.get("title", ""), category=doc.get("category", ""), content=doc.get("content"), bm25_score=doc.get("bm25_score"))
        for doc in raw_docs
    ]
    return issues, docs_used, count_patterns_checked(language)


from typing import Generator  # noqa: E402

def run_streaming(
    code: str,
    language: str,
    retriever: "BM25Retriever",
    emit: Callable[[str, dict], None],
) -> tuple[List[Issue], List[DocUsed], int]:
    """
    Giống run() nhưng gọi emit(stage, data) sau mỗi bước để stream tiến trình.
    emit("step", {"stage": ..., "status": "running"|"done", ...})
    emit("result", {"issues": [...], "docs_used": [...]})
    """
    # ── Bước 1: Race pattern detector (regex nhanh trước LLM) ──
    emit("step", {"stage": "race_detector", "status": "running", "label": "Scanning race condition patterns…"})
    raw_detections = detectRaceConditions(code, language)
    issues = format_report(raw_detections, code)
    emit("step", {"stage": "race_detector", "status": "done",
                  "label": f"Race detector: {len(issues)} pattern(s) found",
                  "found": [i.pattern_id for i in issues if hasattr(i, "pattern_id")],
                  "detections": [
                      {
                          "pattern_id": i.pattern_id,
                          "line_range": i.line_range,
                          "severity": i.severity,
                          "description": i.description,
                      }
                      for i in issues
                  ]})

    # ── Bước 2: AST keyword extraction ──
    emit("step", {"stage": "ast", "status": "running", "label": "Extracting AST keywords…"})
    query = _extract_keywords(code)
    
    ast_flow = [
        "1. Parse code into AST tree (Esprima)",
        "2. Walk nodes to extract Identifier tokens",
        "3. Filter out JS stopwords (if, for, async...)",
        "4. Retain unique keywords for search"
    ]
    
    emit("step", {"stage": "ast", "status": "done",
                  "label": f"AST keywords: {query[:60]}{'…' if len(query) > 60 else ''}",
                  "keywords": query,
                  "process_flow": ast_flow})

    # ── Bước 3: BM25 search ──
    emit("step", {"stage": "bm25", "status": "running", "label": "Searching knowledge base (BM25)…"})
    raw_docs = retriever.search(query, top_k=1) if query else []

    docs_with_scores = []
    for d in raw_docs:
        docs_with_scores.append({
            "title": d.get("title", ""),
            "score": d.get("bm25_score"),
            "category": d.get("category"),
        })

    emit("step", {"stage": "bm25", "status": "done",
                  "label": f"BM25: {len(raw_docs)} doc(s) retrieved",
                  "docs": docs_with_scores})

    # ── Bước 4: Build prompt ──
    emit("step", {"stage": "prompt", "status": "running", "label": "Building RAG prompt…"})
    prompt = _build_prompt(code, raw_docs)
    emit("step", {"stage": "prompt", "status": "done",
                  "label": f"Prompt ready — {len(prompt)} chars",
                  "chars": len(prompt),
                  "full_prompt": prompt})

    # ── Bước 5: LLM inference — 1 call riêng per issue (xem _generate_fixes_per_issue) ──
    issue_count_label = f"{len(issues)} issue(s)" if issues else "whole file"
    emit("step", {"stage": "llm", "status": "running",
                  "label": f"Sending to ThreadLearn model — {issue_count_label}…"})
    fallback_fix, fallback_explanation = _generate_fixes_per_issue(issues, code, raw_docs, emit=emit)

    if not issues:
        issues = [Issue(
            line_range="all",
            severity="medium",
            description=fallback_explanation or "Phát hiện mã nguồn chưa tối ưu. Hệ thống AI đã cung cấp mã song song hóa an toàn thay thế.",
            fix=fallback_fix,
        )]

    severity_counts = {"high": 0, "medium": 0, "low": 0}
    for iss in issues:
        severity_counts[iss.severity] = severity_counts.get(iss.severity, 0) + 1

    emit("step", {"stage": "llm", "status": "done",
                  "label": f"Model returned {len(issues)} issue(s), each with its own fix",
                  "severity_counts": severity_counts,
                  "fix_chars": sum(len(iss.fix) for iss in issues)})

    docs_used = [
        DocUsed(id=doc.get("id", ""), title=doc.get("title", ""), category=doc.get("category", ""), content=doc.get("content"), bm25_score=doc.get("bm25_score"))
        for doc in raw_docs
    ]
    return issues, docs_used, count_patterns_checked(language)


_RACE_PATTERNS = [
    ("closure_loop_var",   r"\bfor\s*\(\s*var\b"),
    ("double_callback",    r"if\s*\(\s*err\s*\)\s*callback\(err\)\s*;(?!\s*return)"),
    ("sequential_awaits",  r"await\s+\w+[^;]*;\s*\n\s*(?:const\s+\w+\s*=\s*)?await\s+\w+"),
    ("unhandled_rejection",r"async\s+function[^{]*\{(?![\s\S]*try\s*\{)"),
]

import re as _re  # noqa: E402

def _quick_race_scan(code: str) -> list:
    found = []
    for name, pattern in _RACE_PATTERNS:
        if _re.search(pattern, code, _re.MULTILINE):
            found.append(name)
    return found
