# Hướng dẫn chạy Mô hình ThreadLearn qua vLLM (Tối ưu Inference)

Tài liệu này hướng dẫn bạn cách khởi chạy mô hình `cot-v2` (`anha12/threadlearn-qwen2.5-coder-1.5b-merged`) bằng **vLLM** - một engine suy luận cực kỳ nhanh, hỗ trợ PagedAttention và Continuous Batching.

Việc sử dụng vLLM có thể giảm thời gian sinh token (generation time) từ 30s xuống chỉ còn 2-4s, giúp giải quyết triệt để tình trạng chậm chạp của CoT.

## 1. Cài đặt vLLM

Nếu bạn đang chạy trên **Kaggle**, **Google Colab** hoặc máy Linux có GPU (như Ubuntu, WSL2 trên Windows), hãy chạy lệnh sau:

```bash
pip install vllm
```

*(Lưu ý: vLLM chưa hỗ trợ hoàn hảo trên Windows Native, nếu bạn dùng Windows, hãy sử dụng WSL2 hoặc triển khai trực tiếp trên Kaggle).*

## 2. Khởi chạy vLLM Server (OpenAI Compatible)

Mở một Terminal mới (hoặc một cell trong Kaggle) và chạy lệnh:

```bash
python -m vllm.entrypoints.openai.api_server \
    --model anha12/threadlearn-qwen2.5-coder-1.5b-merged \
    --host 0.0.0.0 \
    --port 8000 \
    --max-model-len 2048 \
    --gpu-memory-utilization 0.9
```

Lệnh này sẽ tải mô hình vào GPU và mở một máy chủ cục bộ tại `http://localhost:8000/v1` bắt chước chính xác API của OpenAI.

## 3. Cấu hình Backend Server

Trong dự án `ThreadLearn`, hãy mở file `.env` (tại thư mục `server/server/.env`) và cấu hình như sau:

```env
# Kích hoạt provider openai (bởi vì vLLM đang giả lập OpenAI API)
LLM_PROVIDER=openai

# Trỏ URL về server vLLM cục bộ
OPENAI_BASE_URL=http://localhost:8000/v1

# Tên model (phải khớp với tham số --model ở bước 2)
OPENAI_MODEL_NAME=anha12/threadlearn-qwen2.5-coder-1.5b-merged

# API Key có thể để trống hoặc điền bất kỳ chuỗi nào vì vLLM cục bộ không check key
OPENAI_API_KEY=dummy_key
```

## 4. Giải thích Tối ưu hóa (Stop Words)

Trong file `llm_client.py`, hệ thống đã được cấu hình sẵn tính năng ngắt tự động (Early Truncation):

```python
"stop": ["</thought>", "```\n\n"] 
```

Khi mô hình sinh xong phần code (dấu đóng block \`\`\`), API sẽ tự động ngắt kết nối. Điều này giúp mô hình không lãng phí tài nguyên để sinh ra các đoạn giải thích thừa thãi ở cuối, giảm thiểu độ trễ xuống mức tối đa.
 
