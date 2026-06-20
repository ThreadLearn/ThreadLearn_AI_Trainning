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

if TYPE_CHECKING:
    from bm25_module import BM25Retriever

# AST-based keyword extraction từ AI1
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ai1", "modules"))
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

    Dùng ast_preprocessor.extract_keywords() (esprima AST):
        - Chỉ lấy Identifier tokens thật — tên hàm, tên biến, API calls
        - Bỏ JS keywords (if/for/const/async...) chính xác hơn regex
        - Giữ nguyên CamelCase (setTimeout, Promise, appendFile)
          để khớp với BM25 index đã tách CamelCase

    Fallback sang tokenize() nếu esprima không có.

    Ví dụ:
        code = "setTimeout(() => { sharedVar++; }, 100);"
        tokenize()          → "set timeout shared var"   (tách CamelCase, loãng)
        ast extract_keywords → "setTimeout sharedVar"    (giữ nguyên, khớp tốt hơn)
    """
    if _HAS_AST:
        kw = _ast_extract_keywords(code, language="javascript")
        if kw.strip():
            return kw
    # Fallback
    return " ".join(tokenize(code)[:20])


# ---------------------------------------------------------------------------
# Prompt Builder
# ---------------------------------------------------------------------------

def _build_prompt(code: str, docs: list) -> str:
    """
    Ghép code + context docs thành prompt gửi LLM.

    Format:
        [Context docs]
        ---
        [Code cần phân tích]
        ---
        [Instruction]
    """
    context_parts = []
    for i, doc in enumerate(docs, 1):
        context_parts.append(
            f"Tài liệu {i} — {doc.get('title', '')} [{doc.get('category', '')}]:\n"
            f"{doc.get('content', '')}"
        )

    context = "\n\n".join(context_parts)

    return (
        f"Dưới đây là các tài liệu tham khảo về lập trình concurrent JavaScript:\n\n"
        f"{context}\n\n"
        f"---\n\n"
        f"Code cần phân tích:\n```javascript\n{code}\n```\n\n"
        f"---\n\n"
        f"Dựa vào tài liệu tham khảo, hãy phân tích code trên và liệt kê "
        f"các vấn đề race condition hoặc lỗi concurrent programming nếu có. "
        f"Với mỗi vấn đề, cho biết: dòng code liên quan, mức độ nghiêm trọng "
        f"(high/medium/low), mô tả vấn đề, và gợi ý sửa."
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run(
    code: str,
    language: str,
    retriever: "BM25Retriever",
) -> tuple[List[Issue], List[DocUsed]]:
    query = _extract_keywords(code)
    raw_docs = retriever.search(query, top_k=3) if query else []
    prompt = _build_prompt(code, raw_docs)   # noqa: F841
    issues = llm_client.analyze_code(code, raw_docs)
    docs_used = [
        DocUsed(id=doc.get("id", ""), title=doc.get("title", ""), category=doc.get("category", ""))
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
    race_patterns = _quick_race_scan(code)
    emit("step", {"stage": "race_detector", "status": "done",
                  "label": f"Race detector: {len(race_patterns)} pattern(s) found",
                  "found": race_patterns})

    # ── Bước 2: AST keyword extraction ──
    emit("step", {"stage": "ast", "status": "running", "label": "Extracting AST keywords…"})
    query = _extract_keywords(code)
    emit("step", {"stage": "ast", "status": "done",
                  "label": f"AST keywords: {query[:60]}{'…' if len(query) > 60 else ''}",
                  "keywords": query})

    # ── Bước 3: BM25 search ──
    emit("step", {"stage": "bm25", "status": "running", "label": "Searching knowledge base (BM25)…"})
    raw_docs = retriever.search(query, top_k=3) if query else []
    doc_titles = [d.get("title", "") for d in raw_docs]
    emit("step", {"stage": "bm25", "status": "done",
                  "label": f"BM25: {len(raw_docs)} doc(s) retrieved",
                  "docs": doc_titles})

    # ── Bước 4: Build prompt ──
    emit("step", {"stage": "prompt", "status": "running", "label": "Building RAG prompt…"})
    prompt = _build_prompt(code, raw_docs)
    print("\n" + "="*60)
    print(f"[PROMPT] {len(prompt)} chars")
    print(prompt)
    print("="*60 + "\n")
    emit("step", {"stage": "prompt", "status": "done", "label": "Prompt ready"})

    # ── Bước 5: LLM inference ──
    emit("step", {"stage": "llm", "status": "running", "label": "Sending to ThreadLearn model (HF Space)…"})
    issues = llm_client.analyze_code(code, raw_docs)
    emit("step", {"stage": "llm", "status": "done",
                  "label": f"Model returned {len(issues)} issue(s)"})

    docs_used = [
        DocUsed(id=doc.get("id", ""), title=doc.get("title", ""), category=doc.get("category", ""))
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
