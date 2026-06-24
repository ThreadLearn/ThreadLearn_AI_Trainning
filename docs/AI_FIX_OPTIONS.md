# CÁC PHƯƠNG ÁN CẢI THIỆN MÔ HÌNH QWEN2.5-CODER (Khắc phục File Append, Zalgo, Buffer Leak)

## 1. Phương án 1: Bật lại tính năng RAG (Khuyên dùng)
- **Bản chất:** Bật lại Retrieval-Augmented Generation (BM25) trong lúc Test để cung cấp Context cho AI.
- **Ưu điểm:** Phản ánh đúng 100% môi trường Production của dự án. Không cần tốn thêm công sức Train lại mô hình. Cung cấp ngay giải pháp mẫu cho AI copy.

## 2. Phương án 2: Tăng cường độ Train (Tăng Epochs)
- **Bản chất:** Chạy lại Kaggle Training với `num_train_epochs` = 8 hoặc 10 (thay vì 3) để ép model ghi nhớ các cấu trúc phức tạp.
- **Ưu điểm:** Rất dễ thực hiện (chỉ cần đổi tham số).
- **Nhược điểm:** Rủi ro Overfitting nhẹ trên tập dữ liệu.

## 3. Phương án 3: Prompt Engineering (Nhắc bài)
- **Bản chất:** Đổi System Prompt từ `Convert to concurrent JavaScript:` thành `Fix concurrency bugs (Race conditions, Zalgo, Buffer Leaks) in the following code:`.
- **Ưu điểm:** Kích hoạt đúng trọng số của nơ-ron liên quan đến lỗi, giúp tỷ lệ Pass tăng vọt tức thì.

## 4. Phương án 4: Huấn luyện tư duy theo bước (Chain-of-Thought - CoT)
- **Bản chất:** Sửa lại Dataset để AI phải sinh ra comment giải thích lỗi trước khi sinh code (Ví dụ: `// Lỗi Zalgo. Cách sửa: dùng process.nextTick...`).
- **Ưu điểm:** Phương pháp hiện đại nhất giúp các model nhỏ (1.5B) đạt tư duy của model lớn. Giải quyết triệt để sự yếu kém về thay đổi cấu trúc code.
- **Nhược điểm:** Tốn công sinh lại toàn bộ Dataset theo chuẩn CoT.
