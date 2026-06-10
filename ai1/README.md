# ThreadLearn AI1 - Mô hình Sửa lỗi Node.js

Thư mục này chứa toàn bộ pipeline thu thập dữ liệu, tiền xử lý và huấn luyện mô hình ngôn ngữ (LLM) chuyên dụng cho việc dò tìm và tự động sửa các lỗi liên quan đến Concurrency trong Node.js.

## 1. Mục tiêu
- Tạo ra một mô hình nhỏ gọn (1.5B) nhưng có khả năng phân tích ngữ cảnh của JavaScript/Node.js tương đương với GPT-3.5 trong khía cạnh bất đồng bộ.
- Nhận diện và sửa các lỗi: Race Condition, Event Loop Blocking, Callback Hell, Promise Floating, Memory Leak.

## 2. Kiến trúc & Cấu hình Huấn luyện

### 2.1. Base Model
- **Model:** `Qwen/Qwen2.5-Coder-1.5B`
- **Lý do chọn:** Kích thước siêu nhẹ (3GB), lý tưởng để chạy Local trên các thiết bị tài nguyên thấp thông qua Ollama/Llama.cpp, nhưng có năng lực lập trình vượt trội nhờ kiến trúc Qwen2.5.

### 2.2. Kỹ thuật Fine-tune (QLoRA)
- **Quantization:** 4-bit (NF4) với `bnb_4bit_use_double_quant=True`.
- **LoRA Config:** `r=16`, `alpha=32`, target_modules `["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]`.
- **Hyperparameters:**
  - `learning_rate`: 2e-4
  - `batch_size`: 1 (gradient_accumulation_steps=8)
  - `scheduler`: Cosine
  - `epochs/steps`: 500 steps.
  - `optimizer`: paged_adamw_32bit
  - `dtype`: Float16 / BFloat16 tùy kiến trúc phần cứng (T4 dùng fp16).

## 3. Quản lý Dữ liệu (Dataset)
- **Nguồn:** BugsJS và các bài test tổng hợp (Synthetic).
- **Quy mô:** ~700-1000 cặp `(input_code, target_code)`.
- **Pipeline Xử lý:**
  - Thu thập code thô từ Git/Issues.
  - Chạy qua AST Parser (sử dụng `@babel/parser`) để loại bỏ comment, chuẩn hóa format (xoá bỏ các yếu tố gây nhiễu).
  - Biên dịch thành định dạng JSONL chuyên dụng cho chuẩn SFTTrainer.

## 4. Kết quả Đánh giá
Mô hình đã được thử nghiệm trên 20 test cases khét tiếng nhất của JS. 
- **Tỉ lệ Pass:** 80-90% (18/20).
- **Thành tựu:**
  - Biết dùng `Promise.all` để tăng tốc I/O.
  - Biết dùng "Batching/Chunking" để chống nghẽn mạng và rò rỉ RAM khi tải hàng vạn URLs.
  - Chống Context Loss bằng Arrow Functions.
  - Tự thêm `.catch(next)` trong môi trường Express.js.

*(Chi tiết xem thêm tại `docs/EVALUATION_REPORT.md`)*

## 5. Tích hợp Backend
Bộ não của AI1 đã được "ráp" thành công vào Backend thông qua Hugging Face Inference API. 
Xem chi tiết các logic Parser tại `ai2/server/output_parser.py` và `ai2/server/llm_client.py`.
