"""
AI2-05: LLM Client — Mock implementation.
Trả hardcoded response để FE unblock ngay.

AI2-08: Swap sang OpenAI/Ollama thật mà không cần sửa rag_pipeline.py.
Strategy pattern: rag_pipeline chỉ gọi analyze_code(), không biết LLM là mock hay thật.
"""

from typing import List, Dict, Any

from config import LLM_PROVIDER
from schemas import Issue


# ---------------------------------------------------------------------------
# Mock LLM (dùng ngay bây giờ)
# ---------------------------------------------------------------------------

def _mock_analyze(code: str, context_docs: List[Dict[str, Any]]) -> List[Issue]:
    """
    Mock response — trả 1 issue cứng để FE có data test UI.
    Sẽ bị xóa khi AI2-08 hoàn thành.
    """
    return [
        Issue(
            line_range="1-10",
            severity="medium",
            description=(
                "[MOCK] Phát hiện khả năng race condition: "
                "biến shared có thể bị modify đồng thời bởi nhiều callback."
            ),
            fix=(
                "Dùng Promise.all() để kiểm soát luồng, "
                "hoặc Mutex/Semaphore nếu cần exclusive access."
            ),
        )
    ]


# ---------------------------------------------------------------------------
# OpenAI client (AI2-08 — chưa implement)
# ---------------------------------------------------------------------------

def _openai_analyze(code: str, context_docs: List[Dict[str, Any]]) -> List[Issue]:
    """
    [AI2-08] Gọi OpenAI GPT-3.5-turbo với RAG context.
    Chưa implement — raise NotImplementedError để biết khi nào gọi nhầm.
    """
    raise NotImplementedError(
        "OpenAI client chưa implement. "
        "Set LLM_PROVIDER=mock trong .env để dùng mock tạm."
    )


# ---------------------------------------------------------------------------
# Ollama client (AI2-08 — chờ SafeTensors từ Ân)
# ---------------------------------------------------------------------------

def _ollama_analyze(code: str, context_docs: List[Dict[str, Any]]) -> List[Issue]:
    """
    [AI2-08] Gọi Ollama local model (fine-tuned từ AI1).
    Blocked: cần SafeTensors từ AI1-07 (Ân).
    """
    raise NotImplementedError(
        "Ollama client chưa implement. "
        "Blocked on AI1-07 (SafeTensors from Ân)."
    )


# ---------------------------------------------------------------------------
# Public API — rag_pipeline.py gọi hàm này
# ---------------------------------------------------------------------------

def analyze_code(code: str, context_docs: List[Dict[str, Any]]) -> List[Issue]:
    """
    Phân tích code và trả về danh sách Issue.

    Tự động chọn provider dựa trên LLM_PROVIDER trong .env:
        mock   → _mock_analyze()     ← mặc định hiện tại
        openai → _openai_analyze()   ← AI2-08
        ollama → _ollama_analyze()   ← AI2-08, blocked on AI1-07

    Args:
        code:         source code cần phân tích
        context_docs: top-3 docs từ BM25 search (đã có title + content)

    Returns:
        List[Issue] — rỗng nếu không phát hiện vấn đề
    """
    provider = LLM_PROVIDER.lower()

    if provider == "openai":
        return _openai_analyze(code, context_docs)
    elif provider == "ollama":
        return _ollama_analyze(code, context_docs)
    else:
        # Mặc định: mock (bao gồm LLM_PROVIDER=mock hoặc chưa set)
        return _mock_analyze(code, context_docs)
