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

import asyncio
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Query, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from auth import get_current_user
from bm25_module import load_retriever
from schemas import (
    AnalyzeRequest, AnalyzeResponse,
    AnalysisRecord, HistoryResponse,
    HealthResponse,
)
import rag_pipeline
import cache
import db
from config import LLM_PROVIDER

# ---------------------------------------------------------------------------
# AI2-10: Concurrency control — giới hạn 3 LLM call đồng thời
# Lý do: Ollama/GPU OOM nếu >3 inference song song; OpenAI rate-limit friendly
# ---------------------------------------------------------------------------
_llm_semaphore = asyncio.Semaphore(3)
LLM_TIMEOUT_SECONDS = 180  # HF Space CPU inference ~2-3 phút


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
    await db.ensure_indexes()
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

    Lưu ý: MongoDB persistence (AIHistory) do Node.js backend đảm nhiệm
    sau khi nhận response này, không phải trách nhiệm của service này.
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

    # Step 3: Cache MISS → chạy RAG pipeline với concurrency control
    # Semaphore(3): tối đa 3 LLM call đồng thời — tránh GPU OOM / rate limit
    # asyncio.timeout(30): trả 504 nếu LLM treo quá 30 giây
    if not _llm_semaphore._value and _llm_semaphore.locked():   # type: ignore[attr-defined]
        raise HTTPException(
            status_code=429,
            detail={"error": "queue_full", "retry_after": 10},
        )
    try:
        async with asyncio.timeout(LLM_TIMEOUT_SECONDS):
            async with _llm_semaphore:
                issues, docs_used, patterns_checked = await asyncio.to_thread(
                    rag_pipeline.run,
                    body.code,
                    body.language,
                    retriever,
                )
    except TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="LLM analysis timed out. Please try again.",
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
        patterns_checked=patterns_checked,
    )

    # Step 4: Lưu vào Redis (graceful — lỗi không ảnh hưởng response)
    await cache.set_cached(body.code, body.language, response)

    # Step 5: Lưu vào MongoDB (AI2-09) — graceful degradation
    await db.save_analysis(
        user_id=user_id,
        input_code=body.code,
        language=body.language,
        issues=[i.model_dump() for i in issues],
        docs_used=[d.model_dump() for d in docs_used],
        model=LLM_PROVIDER,
        cached=False,
    )

    return response


@app.post(
    "/api/v1/ai/analyze/stream",
    tags=["AI Analysis"],
    summary="Stream tiến trình phân tích real-time (SSE)",
)
async def analyze_stream(
    body: AnalyzeRequest,
    user_id: str = Depends(get_current_user),
):
    """
    Server-Sent Events stream — emit từng bước pipeline:
      race_detector → ast → bm25 → prompt → llm → result
    """
    retriever = app.state.retriever

    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue()

        def emit(event: str, data: dict):
            queue.put_nowait((event, data))

        async def run_pipeline():
            try:
                async with asyncio.timeout(LLM_TIMEOUT_SECONDS):
                    async with _llm_semaphore:
                        issues, docs_used, patterns_checked = await asyncio.to_thread(
                            rag_pipeline.run_streaming,
                            body.code,
                            body.language,
                            retriever,
                            emit,
                        )
                result_data = {
                    "issues": [i.model_dump() for i in issues],
                    "docs_used": [d.model_dump() for d in docs_used],
                    "cached": False,
                    "user_id": user_id,
                    "language": body.language,
                    "patterns_checked": patterns_checked,
                }
            except TimeoutError:
                queue.put_nowait(("error", {"message": "LLM analysis timed out."}))
                return
            except Exception as exc:
                queue.put_nowait(("error", {"message": str(exc)}))
                return
            else:
                queue.put_nowait(("result", result_data))
                queue.put_nowait(("done", {}))

        task = asyncio.create_task(run_pipeline())

        while True:
            event, data = await queue.get()
            yield f"event: {event}\ndata: {json.dumps(data)}\n\n"
            if event in ("done", "error"):
                break

        await task

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get(
    "/api/v1/ai/history/{user_id}",
    response_model=HistoryResponse,
    tags=["AI Analysis"],
    summary="Lịch sử phân tích của user",
)
async def get_history(
    user_id: str,
    current_user: str = Depends(get_current_user),
    page: int = Query(default=1, ge=1, description="Trang (bắt đầu từ 1)"),
    limit: int = Query(default=20, ge=1, le=100, description="Số bản ghi mỗi trang"),
):
    """
    Trả về lịch sử phân tích của user_id, phân trang.

    Bảo mật: user chỉ xem được lịch sử của chính mình.
    Sắp xếp: mới nhất trước (created_at DESC).

    Query params:
        page  — trang hiện tại, mặc định 1
        limit — số bản ghi mỗi trang, mặc định 20, tối đa 100
    """
    if current_user != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Không có quyền xem lịch sử của user khác",
        )

    records, total = await db.get_history(user_id=user_id, page=page, limit=limit)

    analyses = [
        AnalysisRecord(
            analysis_id=r["analysis_id"],
            language=r["language"],
            issues_count=r["issues_count"],
            created_at=r["created_at"],
        )
        for r in records
    ]

    return HistoryResponse(
        user_id=user_id,
        analyses=analyses,
        total=total,
        page=page,
        limit=limit,
    )
