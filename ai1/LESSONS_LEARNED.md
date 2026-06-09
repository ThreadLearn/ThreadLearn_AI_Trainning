# Lessons Learned (Kinh nghiệm rút ra từ AI1)

Dưới đây là tài liệu nội bộ ghi chép lại các bài học xương máu trong quá trình xây dựng và huấn luyện Mô hình ThreadLearn-Qwen2.5-Coder.

## 1. Vấn đề Chất lượng Dữ liệu (Garbage In, Garbage Out)
**Sự cố:** 
Ở những lượt train đầu tiên, mô hình học thuộc lòng cả các "comment nhảm" của lập trình viên và các khoảng trắng không cần thiết. Thậm chí đôi khi nó trả về kết quả kèm theo console.log rác.

**Bài học:**
- Dữ liệu thô từ Git/GitHub luôn cần qua bước tiền xử lý mạnh tay.
- Việc áp dụng AST (Abstract Syntax Tree) thông qua `@babel/parser` là một bước ngoặt. Thay vì dùng Regex cắt ghép thủ công, AST giúp ta bóc tách chính xác cấu trúc hàm, xóa comment an toàn và chuẩn hóa format. Điều này khiến dung lượng dataset giảm nhưng chất lượng "tinh khiết" tăng đột biến.

## 2. Phần cứng và Cấu hình Quantization
**Sự cố:**
Huấn luyện mô hình 1.5B tham số trên Kaggle (GPU T4 với 16GB VRAM) liên tục bị Out of Memory (OOM) hoặc dính lỗi `NotImplementedError` từ `torch.bfloat16`.

**Bài học:**
- GPU Tesla T4 (đời cũ) **không hỗ trợ kiến trúc BFloat16 (`bf16=True`)**. Việc để mặc định `bf16=True` trong SFTTrainer sẽ gây sập. Giải pháp là ép kiểu về `fp16=True` hoặc `float16`.
- Để tránh OOM, phải tuân thủ nghiêm ngặt kỹ thuật **QLoRA 4-bit**.
- **Batch Size:** Không bao giờ được đặt `per_device_train_batch_size` lớn hơn 1 khi train trên T4. Thay vào đó, tăng `gradient_accumulation_steps=8` để bù lại lượng batch size cần thiết cho quá trình hội tụ gradient. (Tương tự, `per_device_eval_batch_size` cũng phải hạ xuống 1).

## 3. Lỗi Lặp Từ (Repetition) lúc Inference
**Sự cố:**
Khi gọi Hugging Face API để chạy thử 20 bài test, mô hình trả về đoạn code đúng, nhưng sau đó lại tự động in lặp lại đoạn code đó 3-4 lần liên tục cho đến khi cạn `max_new_tokens`.

**Bài học:**
- Nguyên nhân gốc là do lúc tạo file JSONL Train, cặp `{prompt}{completion}` được nối liền vào nhau mà không có các token ngắt kết thúc như `<|im_end|>` hoặc `[DONE]`. Mô hình không học được lúc nào phải dừng bút.
- **Cách khắc phục Tạm thời:** Thêm `repetition_penalty=1.1` vào tham số cấu hình lúc sinh văn bản (generate).
- **Cách khắc phục Triệt để:** Xây dựng một module `output_parser.py` (Parser) ở tầng Backend FastAPI để cắt bỏ tất cả các dòng lặp lại dư thừa, chỉ trích xuất khối code (Code block) đầu tiên.

## 4. Quản lý Token và Bảo mật (Secret Scanning)
**Sự cố:**
Lỗi không thể Push code lên GitHub do dính `HF_TOKEN` và `GITHUB_TOKEN` trực tiếp trong file mã nguồn. 

**Bài học:**
- GitHub Secret Scanning cực kỳ nhạy. Việc để lộ Hugging Face Token sẽ ngay lập tức bị chặn Push.
- Luôn luôn sử dụng `os.environ.get("TOKEN")` và cung cấp qua `.env`.
- Với Kaggle, bắt buộc phải dùng công cụ **Kaggle Secrets** (`UserSecretsClient()`) thay vì hardcode biến môi trường.

## 5. Tầm quan trọng của bước Merge Model (AI1-07)
**Sự cố:**
Nhầm lẫn việc đẩy Adapter (LoRA) là đã hoàn tất mô hình.

**Bài học:**
- File do SFTTrainer xuất ra mặc định (dạng safetensors 30-50MB) chỉ chứa các "thông số khác biệt" (weights update). Nó không thể chạy độc lập với Llama.cpp hoặc Ollama.
- Bắt buộc phải thực hiện bước `merge_and_unload()` với Base Model ở chuẩn `float16` (bằng cách offload sang CPU nếu thiếu VRAM) để tạo ra một khối kiến trúc hợp nhất dung lượng 3GB thì mới có thể sử dụng rộng rãi được.
