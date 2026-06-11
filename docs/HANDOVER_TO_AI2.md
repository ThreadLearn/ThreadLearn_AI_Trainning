# Bàn giao Tích hợp Backend (AI1 -> AI2)

Chào Trung (AI2),

Phía AI1 đã hoàn tất việc Fine-tune mô hình chuyên sửa lỗi bất đồng bộ (Race Condition, Event Loop Blocking) cho Node.js và đã tích hợp thành công vào Backend FastAPI. 

Dưới đây là các đầu việc phía AI1 đã hỗ trợ code giúp bạn (Tasks **AI2-08** & **AI1-08**), bạn có thể lấy code về và chạy tiếp các luồng của AI2 (Frontend/RAG) mà không lo bị nghẽn (blocked) nữa nhé:

## 1. Những file đã cập nhật / tạo mới
- **Tạo mới `ai2/server/output_parser.py`**:
  - Chức năng: Tiền xử lý kết quả thô từ Mô hình AI trả về. Cắt bỏ lỗi lặp code (repetition) của model Qwen, trích xuất đúng 1 khối code chuẩn xác.
  - Đóng gói đoạn code vừa trích xuất thành Data Model `Issue` (`line_range="all"`, `severity="high"`, `fix="<code block>"`).

- **Cập nhật `ai2/server/llm_client.py`**:
  - Đã tích hợp thành công hàm `_ollama_analyze` để gọi trực tiếp tới **Hugging Face Inference API**.
  - Đã làm sẵn cấu trúc dự phòng cho `_openai_analyze` (phòng khi bạn cần test so sánh với GPT-3.5).

## 2. Thông tin API & Token (Dùng ngay)
Hiện tại, code trong `llm_client.py` đã được cấu hình cứng với API URL và Token dưới đây để bạn test. Khi nào đưa lên production, bạn nhớ chuyển `HF_TOKEN` vào file `.env` nhé.

```python
# API URL gọi tới Mô hình Qwen2.5-Coder-1.5B đã được fine-tune bởi AI1
API_URL = "https://api-inference.huggingface.co/models/anha12/threadlearn-qwen2.5-coder-1.5b"

# Token cấp quyền Read từ Hugging Face (Vui lòng liên hệ AI1 để lấy hoặc tự điền)
HEADERS = {
    "Authorization": "Bearer <YOUR_HF_TOKEN_HERE>",
    "Content-Type": "application/json"
}
```

## 3. Xác nhận chất lượng
Mô hình đã được pass qua 20 bộ Test hóc búa nhất về Concurrency (có ghi chú trong `docs/EVALUATION_REPORT.md`). 
- Có khả năng Fix Floating Promises.
- Có khả năng gom các chuỗi tuần tự thành `Promise.all()` (Chunking).
- Giải quyết gọn gàng các lỗi Context Loss và Buffer Leak.

Bạn chỉ việc test gọi hàm `analyze_code(code, context_docs)` từ `rag_pipeline.py` là sẽ thấy phép màu!

## 4. [QUAN TRỌNG] Nâng cấp `ast_preprocessor.py` (Babel AST cho JavaScript)
Dành cho RAG Pipeline của AI2:
- Trước đây file `ai1/modules/ast_preprocessor.py` dùng thư viện `ast` để xử lý code Python, nhưng lại dùng **Regex (biểu thức chính quy)** để fallback khi bóc tách code JavaScript (ngôn ngữ chính của dự án). Điều này dẫn đến lỗi khi đọc arrow functions hoặc nested blocks khó.
- **AI1 đã khắc phục hoàn toàn:** Tôi đã viết file `ai1/modules/js_ast_helper.js` dùng chuẩn `@babel/parser` của Node.js. Giờ đây `ast_preprocessor.py` sẽ tự động gọi ngầm (subprocess) Node.js mỗi khi cần phân tích code JavaScript (để extract keywords, functions, strip comments).
- **Trạng thái:** Không còn dùng Regex lậu nữa! Giờ đây hệ thống RAG của bạn sẽ lập chỉ mục (index) các file code JavaScript cực kỳ chuẩn xác 100%.

Chúc bạn hoàn thành tốt các task còn lại của AI2 nhé!
*(Từ 팀 AI1 - ThreadLearn)*
