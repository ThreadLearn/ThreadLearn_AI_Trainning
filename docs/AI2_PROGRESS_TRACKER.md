# THÔNG TIN TASK (AI2 PROGRESS TRACKER)

| UC ID | Task | Mô tả | Output / Deliverable | Status | Priority | Phụ thuộc |
|---|---|---|---|---|---|---|
| **AI2-02** | BM25 Indexing Module | Tích hợp thuật toán BM25 để tìm kiếm ngữ nghĩa trong Knowledge Base (`knowledge_base.json`). | `bm25_module.py` | ✅ Done | 🔴 High | — |
| **AI2-03** | Race Condition Detector | Phân tích tĩnh code để cảnh báo các vùng dễ xảy ra race condition. | `race_detector.py` | ✅ Done | 🔴 High | AST Parser (AI1-03) |
| **AI2-04** | Report Formatter | Chuẩn hóa kết quả trả về từ RAG và Race Detector thành JSON Schema chuẩn xác. | `report_formatter.py` | ✅ Done | 🟡 Med | — |
| **AI2-05** | FastAPI Server & Auth | Dựng API gateway (`/analyze`, `/history`), xác thực JWT, định nghĩa Pydantic Schemas. | `main.py`, `auth.py`, `schemas.py` | ✅ Done | 🔴 High | — |
| **AI2-06** | RAG Pipeline | Luồng chính: Nhận Code -> Dùng BM25 tìm Docs -> Build Prompt -> Gọi LLM -> Trả kết quả. | `rag_pipeline.py` | ✅ Done | 🔴 High | AI2-02, AI2-05 |
| **AI2-07** | Redis Caching Layer | Lưu kết quả phân tích theo SHA256 code để tăng tốc độ phản hồi (`<100ms`). | `cache.py` | ✅ Done | 🟡 Med | — |
| **AI2-08** | Swap LLM OpenAI/Ollama | Cắm API gọi LLM thật (OpenAI GPT-3.5) hoặc Ollama chạy model local thay cho code Mock. | `llm_client.py` | ⏳ To Do | 🔴 High | AI1-07 (Chờ mô hình AI1) |
| **AI2-09** | MongoDB Persistence | Lưu trữ toàn bộ lịch sử phân tích của người dùng xuống Database. | `db.py` | ✅ Done | 🟡 Med | — |
| **AI2-10** | Concurrency Control | Cấu hình Semaphore giới hạn 3 LLM calls đồng thời để chống quá tải GPU / Rate limit API. | `main.py` | ✅ Done | 🟢 Low | — |

---
*Ghi chú: Bảng theo dõi tiến độ Task của team AI2 (Trung). Hệ thống Backend cơ bản đã code xong 90%, hiện tại module gọi LLM thật (AI2-08) đang tạm dùng Mock để chờ nhận trọng số model (SafeTensors) từ quá trình Fine-tune của AI1.*
