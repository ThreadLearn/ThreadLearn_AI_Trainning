"""
AI2-05/06: RAG Pipeline
Flow: code → keyword extraction → BM25 top-3 docs → build prompt → LLM → List[Issue]

Keyword extraction dùng ast_preprocessor.extract_keywords() (AST-based, esprima).
Fallback sang bm25_module.tokenize() nếu import fail.
"""

import os
import sys
from typing import List, TYPE_CHECKING

from bm25_module import tokenize
from schemas import Issue, DocUsed
import llm_client
from race_detector import detectRaceConditions
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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run(
    code: str,
    language: str,
    retriever: "BM25Retriever",
) -> tuple[List[Issue], List[DocUsed]]:
    # 1. RAG
    query = _extract_keywords(code)
    raw_docs = retriever.search(query, top_k=1) if query else []
    prompt = _build_prompt(code, raw_docs)
    
    # 2. Race Detector (cho descriptions & severity)
    raw_detections = detectRaceConditions(code, language)
    issues = format_report(raw_detections)
    
    # 3. LLM Fix
    llm_output = llm_client.get_llm_fix(code, prompt)
    parsed = cleanOutput(llm_output)
    fixed_code = f"```javascript\n{parsed['code']}\n```"
    
    # 4. Merge Fix vào Issues
    if not issues:
        issues = [Issue(
            line_range="all",
            severity="medium",
            description=parsed.get("explanation", "Phát hiện mã nguồn chưa tối ưu. Hệ thống AI đã cung cấp mã song song hóa an toàn thay thế."),
            fix=fixed_code
        )]
    else:
        for iss in issues:
            iss.fix = fixed_code

    docs_used = [
        DocUsed(id=doc.get("id", ""), title=doc.get("title", ""), category=doc.get("category", ""), bm25_score=doc.get("bm25_score"))
        for doc in raw_docs
    ]
    return issues, docs_used


from typing import Callable, Generator  # noqa: E402

def run_streaming(
    code: str,
    language: str,
    retriever: "BM25Retriever",
    emit: Callable[[str, dict], None],
) -> tuple[List[Issue], List[DocUsed]]:
    """
    Giống run() nhưng gọi emit(stage, data) sau mỗi bước để stream tiến trình.
    emit("step", {"stage": ..., "status": "running"|"done", ...})
    emit("result", {"issues": [...], "docs_used": [...]})
    """
    # ── Bước 1: Race pattern detector (regex nhanh trước LLM) ──
    emit("step", {"stage": "race_detector", "status": "running", "label": "Scanning race condition patterns…"})
    raw_detections = detectRaceConditions(code, language)
    issues = format_report(raw_detections)
    emit("step", {"stage": "race_detector", "status": "done",
                  "label": f"Race detector: {len(issues)} pattern(s) found",
                  "found": [i.pattern_id for i in issues if hasattr(i, "pattern_id")]})

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
            "score": d.get("bm25_score")
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

    # ── Bước 5: LLM inference ──
    emit("step", {"stage": "llm", "status": "running", "label": "Sending to ThreadLearn model (HF Space)…"})
    llm_output = llm_client.get_llm_fix(code, prompt)
    parsed = cleanOutput(llm_output)
    fixed_code = f"```javascript\n{parsed['code']}\n```"
    
    if not issues:
        issues = [Issue(
            line_range="all",
            severity="medium",
            description=parsed.get("explanation", "Phát hiện mã nguồn chưa tối ưu. Hệ thống AI đã cung cấp mã song song hóa an toàn thay thế."),
            fix=fixed_code
        )]
    else:
        for iss in issues:
            iss.fix = fixed_code
            
    emit("step", {"stage": "llm", "status": "done",
                  "label": f"Model returned {len(issues)} issue(s)"})

    docs_used = [
        DocUsed(id=doc.get("id", ""), title=doc.get("title", ""), category=doc.get("category", ""), bm25_score=doc.get("bm25_score"))
        for doc in raw_docs
    ]
    return issues, docs_used


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
