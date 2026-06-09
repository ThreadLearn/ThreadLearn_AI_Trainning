# BÁO CÁO HUẤN LUYỆN MODEL (TRAINING REPORT)

**Dự án:** ThreadLearn (Node.js Concurrency / Async Bug Detector)
**Mô hình gốc (Base Model):** `Qwen/Qwen2.5-Coder-1.5B`
**Trạng thái:** 🚀 Đang huấn luyện trên Kaggle (Epoch ~6 / 500 Steps)

## 1. DỮ LIỆU HUẤN LUYỆN (DATASET)
Toàn bộ tập dữ liệu đã được làm sạch, bổ sung và chuẩn hóa thông qua Data Flow Analysis (AST):

- **Tổng số lượng mẫu:** 783 đoạn mã (Tỉ lệ 90% Train - 10% Eval).
- **Phân bổ:**
  - Tập Huấn luyện (`threadlearn_train.jsonl`): 704 mẫu.
  - Tập Đánh giá (`threadlearn_train_eval.jsonl`): 79 mẫu.
- **Nguồn dữ liệu:**
  - Tự tổng hợp + GitHub/Kaggle code.
  - Dự án **BugsJS**: Khai thác sâu các lỗi thực tế từ hệ sinh thái Node.js (Express, Mongoose, v.v.).
- **Các loại Bug đã được nhúng vào Dataset:**
  1. Race Conditions (Lỗi tương tranh).
  2. Unhandled Promise Rejections (Chết server do không bắt lỗi async).
  3. Callback Hell / Zalgo (Bất đồng bộ không nhất quán).
  4. Deadlocks.
  5. **(New Batch)** Resource Exhaustion (Lỗi `EMFILE` do mở quá nhiều request/file cùng lúc).
  6. **(New Batch)** Lỗi Double Callback (Gây ra `ERR_HTTP_HEADERS_SENT`).
  7. **(New Batch)** Lỗi Context Loss (Mất binding `this` trong callback).
  8. **(New Batch)** Lỗi lệch pha Event Loop (`setTimeout` vs `process.nextTick`).

## 2. KIẾN TRÚC & THAM SỐ HUẤN LUYỆN (HYPERPARAMETERS)
Mô hình được huấn luyện bằng kỹ thuật **QLoRA** (Quantized Low-Rank Adaptation) để tối ưu VRAM.

- **Kỹ thuật Lượng tử hóa (Quantization):** 4-bit (`BitsAndBytes`, `nf4`, double quant).
- **Cấu hình LoRA Adapter:**
  - Rank (`r`): 16
  - Alpha (`lora_alpha`): 32
  - Target Modules: `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`.
- **Tham số SFTTrainer (Training Arguments):**
  - Số bước tối đa (`max_steps`): 500
  - Batch Size (`per_device_train_batch_size`): 2
  - Gradient Accumulation: 4
  - Số mẫu xử lý mỗi bước (Samples per Step): 8
  - Số vòng lặp dự kiến (Epochs): ~5.68 vòng.
  - Optimizer: `paged_adamw_32bit`
  - Learning Rate: `2e-4` với lịch trình `cosine`.
  - Môi trường: Kaggle GPU (T4 x2).

## 3. KẾT QUẢ KỲ VỌNG & BƯỚC TIẾP THEO
- **Kỳ vọng:** Khi quá trình Training đạt mốc 500 steps, Loss sẽ hội tụ ở mức cực thấp, mô hình có khả năng nhìn vào một đoạn code Callback / Sync cũ và in ra **ngay lập tức** đoạn mã thay thế sử dụng `async/await`, `Promise.all()` hoặc `p-limit` chuẩn xác nhất mà không gây chặn Event Loop.
- **Bước tiếp theo:** 
  1. Tải trọng số LoRA Adapter (`final_adapter`) sau khi quá trình trên Kaggle hoàn tất.
  2. Merge trọng số vào Base Model (Qwen2.5-Coder) và xuất file định dạng SafeTensors/GGUF (Task **AI1-07**).
  3. Bàn giao cho team Backend (Trung) để cắm vào Pipeline RAG thông qua Ollama hoặc load nội bộ, hoàn tất API phân tích mã nguồn (Task **AI2-08**).
