"""
AI2-05: FastAPI Server — entry point cho AI microservice.
Owner: AI2 - Trung

Routes:
    POST /api/v1/ai/analyze          — phân tích code (yêu cầu JWT)
    GET  /api/v1/ai/history/{user_id} — lịch sử phân tích (yêu cầu JWT)
    GET  /health                      — health check (public)

Chạy server:
    uvicorn main:app --reload --port 8001
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from auth import get_current_user
from bm25_module import load_retriever
from schemas import (
    AnalyzeRequest, AnalyzeResponse,
    HistoryResponse,
    HealthResponse,
)
import rag_pipeline
import cache


# ---------------------------------------------------------------------------
# Lifespan: load BM25 retriever một lần lúc startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Chạy khi server khởi động:
        - Load knowledge_base.json
        - Build BM25 index (< 500ms với 250 docs)
        - Lưu vào app.state.retriever để mọi request dùng chung

    Chạy khi server tắt:
        - Không cần cleanup (in-memory, GC tự xử lý)
    """
    app.state.retriever = load_retriever()
    yield
    # shutdown: nothing to clean up


# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------

app = FastAPI(
    title="ThreadLearn AI Service",
    description="Race condition detection via BM25 RAG + LLM analysis",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — cho phép Node.js backend và FE dev server gọi
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Restrict to actual origins in production
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """
    Health check — public, không cần JWT.
    Trả về trạng thái server và số doc đang index trong BM25.
    Dùng để: Docker healthcheck, monitoring, FE check server sống không.
    """
    retriever = app.state.retriever
    return HealthResponse(
        status="ok",
        retriever_docs=retriever.doc_count,
    )


@app.post(
    "/api/v1/ai/analyze",
    response_model=AnalyzeResponse,
    tags=["AI Analysis"],
    summary="Phân tích race condition trong code",
)
async def analyze_code(
    body: AnalyzeRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Nhận code từ FE → check Redis cache → (nếu miss) chạy RAG pipeline → trả về danh sách Issue.

    Flow:
        1. JWT verify (Depends(get_current_user))
        2. Check Redis cache (SHA256 key) → HIT: trả ngay, cached=True
        3. MISS: rag_pipeline.run() → issues + docs_used
        4. Lưu kết quả vào Redis (TTL 86400s)
        5. Trả AnalyzeResponse, cached=False

    TODO AI2-09: Lưu kết quả vào MongoDB sau khi phân tích
    """
    retriever = app.state.retriever

    # Step 2: Cache HIT → trả ngay, bỏ qua pipeline
    # get_cached đã có graceful degradation bên trong, nhưng wrap thêm ở đây
    # để đảm bảo bất kỳ exception nào cũng không làm crash route
    try:
        cached_response = await cache.get_cached(body.code, body.language)
    except Exception:
        cached_response = None
    if cached_response is not None:
        cached_response.user_id = user_id   # gán đúng user hiện tại
        return cached_response

    # Step 3: Cache MISS → chạy RAG pipeline
    try:
        issues, docs_used = rag_pipeline.run(
            code=body.code,
            language=body.language,
            retriever=retriever,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline error: {exc}",
        )

    response = AnalyzeResponse(
        user_id=user_id,
        language=body.language,
        issues=issues,
        docs_used=docs_used,
        cached=False,
    )

    # Step 4: Lưu vào Redis (graceful — lỗi không ảnh hưởng response)
    await cache.set_cached(body.code, body.language, response)

    return response


@app.get(
    "/api/v1/ai/history/{user_id}",
    response_model=HistoryResponse,
    tags=["AI Analysis"],
    summary="Lịch sử phân tích của user",
)
def get_history(
    user_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Trả về lịch sử phân tích của user_id.

    Bảo mật: user chỉ xem được lịch sử của chính mình.
    current_user (từ JWT) phải khớp với user_id trong URL.

    TODO AI2-09: Thay mock bằng query MongoDB thật.
    """
    if current_user != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Không có quyền xem lịch sử của user khác",
        )

    # TODO AI2-09: query MongoDB → trả HistoryResponse thật
    return HistoryResponse(
        user_id=user_id,
        analyses=[],
        total=0,
    )
