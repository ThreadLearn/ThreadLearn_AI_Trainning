"""
AI2-05: Pydantic schemas — request/response contracts for FastAPI routes.
All routes import from here. Single source of truth for data shapes.
"""

from typing import List, Literal
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared sub-models
# ---------------------------------------------------------------------------

class Issue(BaseModel):
    """Một vấn đề race condition được phát hiện trong code."""
    line_range: str = Field(
        description="Dòng code liên quan, ví dụ: '12-18' hoặc '42'",
        examples=["12-18", "42"],
    )
    severity: Literal["high", "medium", "low"] = Field(
        description="Mức độ nghiêm trọng: high=nguy hiểm, medium=cần chú ý, low=gợi ý"
    )
    description: str = Field(
        description="Mô tả vấn đề tìm thấy"
    )
    fix: str = Field(
        description="Gợi ý cách sửa"
    )
    pattern_id: str = Field(
        default="unknown",
        description="Pattern identifier, ví dụ: closure_loop_var"
    )


class DocUsed(BaseModel):
    """Tài liệu từ knowledge base được BM25 truy xuất để làm context cho LLM."""
    id: str
    title: str
    category: str


# ---------------------------------------------------------------------------
# POST /api/v1/ai/analyze
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    """Request body gửi lên từ FE (qua Node.js backend)."""
    code: str = Field(
        description="Source code cần phân tích",
        min_length=1,
    )
    language: str = Field(
        default="javascript",
        description="Ngôn ngữ lập trình: 'javascript' | 'typescript'",
    )
    user_id: str = Field(
        description="ID người dùng, dùng để lưu lịch sử (AI2-09)"
    )


class AnalyzeResponse(BaseModel):
    """Response trả về FE sau khi phân tích xong."""
    user_id: str
    language: str
    issues: List[Issue] = Field(
        description="Danh sách vấn đề tìm thấy, rỗng nếu code sạch"
    )
    docs_used: List[DocUsed] = Field(
        description="Top-3 tài liệu BM25 đã dùng làm context"
    )
    cached: bool = Field(
        default=False,
        description="True nếu kết quả lấy từ Redis cache (AI2-07)"
    )


# ---------------------------------------------------------------------------
# GET /api/v1/ai/history/{user_id}
# ---------------------------------------------------------------------------

class AnalysisRecord(BaseModel):
    """Một bản ghi lịch sử phân tích, lưu trong MongoDB (AI2-09)."""
    analysis_id: str
    language: str
    issues_count: int
    created_at: str   # ISO 8601


class HistoryResponse(BaseModel):
    """Response cho route GET /history/{user_id}."""
    user_id: str
    analyses: List[AnalysisRecord] = []
    total: int = 0
    page: int = 1
    limit: int = 20


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    retriever_docs: int = Field(description="Số doc đang được index trong BM25")
