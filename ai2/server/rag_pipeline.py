"""
AI2-05/06: RAG Pipeline
Flow: code → keyword extraction → BM25 top-3 docs → build prompt → LLM → List[Issue]

Keyword extraction hiện tại dùng tokenize() từ bm25_module (đơn giản, không cần AST).
Khi AI1-03 (ast_preprocessor.py từ Ân) hoàn thành → swap vào mà không sửa phần còn lại.
"""

from typing import List, TYPE_CHECKING

from bm25_module import tokenize
from schemas import Issue, DocUsed
import llm_client
from race_detector import detectRaceConditions
from report_formatter import format_report
from output_parser import cleanOutput

if TYPE_CHECKING:
    from bm25_module import BM25Retriever


# ---------------------------------------------------------------------------
# Keyword Extraction
# ---------------------------------------------------------------------------

import sys
import os
# Thêm đường dẫn tới ai1/modules để import ast_preprocessor
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../ai1/modules')))
import ast_preprocessor

def _extract_keywords(code: str) -> str:
    """
    Trích keyword từ code để làm BM25 query.
    Sử dụng Babel AST thực thụ thông qua ast_preprocessor (AI1-03).
    """
    try:
        # Lấy tối đa 20 keywords từ cây AST
        return ast_preprocessor.extract_keywords(code, language="js")
    except Exception as e:
        # Fallback nếu gặp lỗi
        tokens = tokenize(code)
        return " ".join(tokens[:20])



# ---------------------------------------------------------------------------
# Prompt Builder
# ---------------------------------------------------------------------------

def _build_prompt(code: str, docs: list) -> str:
    """
    Ghép code + context docs thành prompt gửi LLM.
    Dùng chuẩn format của eval_rag_merged.py để tránh lỗi hallucination.
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
            f"Dưới đây là các tài liệu tham khảo về lập trình concurrent JavaScript:\n\n"
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
    raw_docs = retriever.search(query, top_k=3) if query else []
    prompt = _build_prompt(code, raw_docs)
    
    # 2. Race Detector (cho descriptions & severity)
    raw_detections = detectRaceConditions(code, language)
    issues = format_report(raw_detections)
    
    # PONYTAIL: Short-circuit nếu không có lỗi, khỏi gọi LLM
    if not issues:
        return [], []
    
    # 3. LLM Fix
    llm_output = llm_client.get_llm_fix(code, prompt)
    parsed = cleanOutput(llm_output)
    fixed_code = f"```javascript\n{parsed['code']}\n```"
    
    # 4. Merge Fix vào Issues
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

    # PONYTAIL: Short-circuit nếu không có lỗi
    if not issues:
        emit("step", {"stage": "llm", "status": "done", "label": "Code an toàn, bỏ qua gọi AI để tối ưu tốc độ."})
        return [], []

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
    raw_docs = retriever.search(query, top_k=3) if query else []
    
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
    print("\n" + "="*60)
    print(f"[PROMPT] {len(prompt)} chars")
    print(prompt)
    print("="*60 + "\n")
    emit("step", {"stage": "prompt", "status": "done",
                  "label": f"Prompt ready — {len(prompt)} chars",
                  "chars": len(prompt),
                  "full_prompt": prompt})

    # ── Bước 5: LLM inference ──
    emit("step", {"stage": "llm", "status": "running", "label": "Sending to ThreadLearn model (HF Space)…"})
    llm_output = llm_client.get_llm_fix(code, prompt)
    parsed = cleanOutput(llm_output)
    fixed_code = f"```javascript\n{parsed['code']}\n```"
    
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
