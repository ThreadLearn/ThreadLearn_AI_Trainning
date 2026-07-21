# ThreadLearn AI1 - Mô hình Sửa lỗi Node.js

Thư mục này chứa toàn bộ pipeline thu thập dữ liệu, tiền xử lý và huấn luyện mô hình ngôn ngữ (LLM) chuyên dụng cho việc dò tìm và tự động sửa các lỗi liên quan đến Concurrency trong Node.js.

## 1. Mục tiêu
- Tạo ra một mô hình nhỏ gọn (1.5B) nhưng có khả năng phân tích ngữ cảnh của JavaScript/Node.js tương đương với GPT-3.5 trong khía cạnh bất đồng bộ.
- Nhận diện và sửa các lỗi concurrency JS qua 5 pattern detector (`race_detector.py`): `closure_loop_var`, `shared_var_settimeout`, `promise_no_await`, `concurrent_write_array`, `counter_no_atomic`. Benchmark cuối cùng bao phủ 10 category bug thực tế (Race Condition, Unhandled Rejection, Double Callback, Resource Exhaustion, Event Loop Blocking, Sequential Awaits, Zalgo, Context Loss, Stream Leak, Callback Hell).

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
- **Quy mô:** 892 cặp `(code, detector_output, reasoning_trace, fix)` — 332 mẫu synthetic viết tay (37.2%) + 560 mẫu generated qua template engine (62.8%, 18 hàm generator × 40 domain slot).
- **Pipeline Xử lý:**
  - Thu thập code thô từ Git/Issues.
  - Chạy qua AST Parser (esprima, JS) để loại bỏ comment, chuẩn hóa format (xoá bỏ các yếu tố gây nhiễu).
  - Biên dịch thành định dạng JSONL chuyên dụng cho chuẩn SFTTrainer.

> Số liệu chi tiết + nguồn gốc dataset: xem [`docs/RESEARCH_LOG.md`](../docs/RESEARCH_LOG.md) và [`docs/my-research/ThreadLearn_ICTA_WordReady.md`](../docs/my-research/ThreadLearn_ICTA_WordReady.md).

## 4. Kết quả Đánh giá

> ⚠️ **Con số "80-90% (18/20)" trong các bản báo cáo cũ KHÔNG có cơ sở thực tế** — nó bị suy ra sai từ unit test dùng mock LLM (`LLM_PROVIDER=mock`), không phải inference thật. Chi tiết lỗi này ở [`README.md`](../README.md#lỗi-5-con-số-1820-90-là-không-có-cơ-sở-thực-tế) mục 8, Lỗi #5.

Kết quả thật, đo bằng inference thật trên model đã merge:

- **Benchmark chính thức — 30-case real-world** (bug thật từ production npm packages): ThreadLearn + pipeline đạt **73.3% (22.0/30)**, vượt GPT-3.5-turbo + cùng pipeline (65.0%). Chi tiết: [`server/tests/real_world/README.md`](../server/tests/real_world/README.md).
- **Benchmark 20-case synthetic** (giai đoạn phát triển sớm hơn): ThreadLearn RAW 70% (14/20), + RAG 75% (15/20).
- **Thành tựu quan sát được:**
  - Biết dùng `Promise.all` để tăng tốc I/O.
  - Biết dùng "Batching/Chunking" để chống nghẽn mạng và rò rỉ RAM khi tải hàng vạn URLs.
  - Chống Context Loss bằng Arrow Functions.
  - Tự thêm `.catch(next)` trong môi trường Express.js.

## 5. Tích hợp Backend
Bộ não của AI1 đã được "ráp" thành công vào Backend thông qua Hugging Face Inference API. 
Xem chi tiết các logic Parser tại `server/server/output_parser.py` và `server/server/llm_client.py`.
