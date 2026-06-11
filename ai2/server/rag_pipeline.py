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
    """
    Chạy toàn bộ RAG pipeline và trả về issues + docs đã dùng.

    Args:
        code:      source code người dùng gửi lên
        language:  "javascript" | "typescript"
        retriever: BM25Retriever đã build (từ app.state.retriever)

    Returns:
        (issues, docs_used)
        issues:    List[Issue] — danh sách vấn đề phát hiện
        docs_used: List[DocUsed] — top-3 docs BM25 đã dùng

    Flow chi tiết:
        Step 1: Trích keyword từ code
                Hiện tại: tokenize() đơn giản
                Sau AI1-03: ast_preprocessor.extract_keywords()

        Step 2: BM25 search top-3 docs từ knowledge_base.json

        Step 3: Build prompt = context docs + code + instruction

        Step 4: Gọi llm_client.analyze_code()
                Hiện tại: mock response
                Sau AI2-08: OpenAI/Ollama thật

        Step 5: Trả về (issues, docs_used)
    """
    # Step 1 — keyword extraction
    query = _extract_keywords(code)

    # Step 2 — BM25 search
    raw_docs = retriever.search(query, top_k=3) if query else []

    # Step 3 — build prompt (prompt được truyền vào LLM, không trả về client)
    prompt = _build_prompt(code, raw_docs)   # noqa: F841 — dùng khi LLM thật

    # Step 4 — LLM call
    issues = llm_client.analyze_code(code, raw_docs)

    # Step 5 — format docs_used để trả về FE
    docs_used = [
        DocUsed(
            id=doc.get("id", ""),
            title=doc.get("title", ""),
            category=doc.get("category", ""),
        )
        for doc in raw_docs
    ]

    return issues, docs_used
