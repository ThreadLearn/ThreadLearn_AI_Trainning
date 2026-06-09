# Báo cáo Đánh giá Mô hình Qwen2.5-Coder-1.5B (ThreadLearn)

**Task:** AI1-06 (Model Evaluation)
**Mô hình Base:** `Qwen/Qwen2.5-Coder-1.5B`
**Phương pháp Fine-tune:** QLoRA (4-bit)
**Tập dữ liệu:** BugsJS (AST-injected)

---

## 1. Kết quả Tổng quan
Qua bộ dữ liệu 20 bài Test (đại diện cho các nhóm lỗi khét tiếng nhất của Node.js), mô hình đạt độ chính xác đáng kinh ngạc trong việc nhận diện và sửa lỗi logic bất đồng bộ.

- **Số test case Pass hoàn toàn:** 18/20
- **Số test case Pass một phần (Cần review):** 2/20
- **Hiện tượng đặc biệt:** Mô hình gặp vấn đề **Lặp code (Repetition)**. Tuy code được sinh ra là chính xác và giải quyết hoàn hảo vấn đề, nhưng đoạn mã đó thường bị in lặp đi lặp lại 3-4 lần do thiếu token `<|im_end|>` trong cấu hình sinh văn bản. (Đã được khắc phục ở tầng Backend bằng `output_parser.py`).

---

## 2. Phân tích chi tiết các nhóm Lỗi

### 2.1. Nhóm lỗi Thắt cổ chai I/O (Sequential Awaits & Missing Promise.all)
Đây là màn trình diễn xuất sắc nhất của mô hình.
- **Vấn đề:** Các lập trình viên thường dùng vòng lặp `for` với `await` bên trong, khiến các truy vấn I/O (ví dụ: gửi email, gọi database) bị thực thi tuần tự, gây lãng phí thời gian chờ.
- **Cách Model fix:** 
  - Tự động phát hiện và gom các thao tác vào mảng.
  - Sử dụng `await Promise.all()` để chạy song song.
  - **Đột phá:** Ở bài test 16 (`downloadAll` 100,000 URLs), model tự động hiểu được việc gọi `Promise.all` trực tiếp sẽ làm sập mạng. Nó đã tự viết thuật toán **Batching/Chunking** bằng lệnh `slice` để giới hạn số lượng request đồng thời (concurrency=4). Tư duy này đạt chuẩn Senior Developer.

### 2.2. Nhóm lỗi Nghẽn Event Loop (Event Loop Blocking)
- **Vấn đề:** Các hàm tính toán nặng (Synchronous Hash, Math) chạy trong vòng lặp lớn chặn đứng luồng chính của Node.js.
- **Cách Model fix:** 
  - Tự động thay thế các hàm Sync (`pbkdf2Sync`, `readFileSync`) thành các hàm Async/Promise.
  - Áp dụng kỹ thuật chia lô để nhường CPU cho Event Loop xử lý các callback khác.

### 2.3. Nhóm lỗi Mất Ngữ Cảnh (Context Loss & Callback Hell)
- **Vấn đề:** Việc dùng `function() {}` trong các callback gây mất ngữ cảnh `this`.
- **Cách Model fix:** Rất nhanh gọn, model tự động đổi tất cả các khai báo `function()` thành Arrow Function `() => {}` để giữ nguyên ngữ cảnh của `this`.
- Model cũng thực hiện việc dẹt hóa (flatten) các Callback Hell bằng `async/await` hoàn toàn chính xác.

### 2.4. Nhóm lỗi Rò rỉ tài nguyên (Buffer Leak / Unhandled Rejection)
- **Vấn đề:** Quên `.catch()` trong các Promise hoặc quên đóng Stream khi lỗi xảy ra.
- **Cách Model fix:** 
  - Trong Express.js (Case 4/11), model tự động chèn thêm tham số `next` vào callback và nối `.catch(next)`, tuân thủ đúng Best Practice của framework.
  - Trong thao tác File Stream (Case 19), nó thêm các bộ lắng nghe sự kiện `rs.on('end')` và `rs.once('error')` để chủ động đóng luồng dữ liệu, dập tắt nguy cơ Memory Leak.

### 2.5. Nhóm lỗi Race Condition (Cạnh tranh tranh chấp)
Đây là nhóm lỗi khó nhất. 
- Mặc dù model đã chuyển đổi các luồng Floating Promise thành các luồng có kiểm soát (dùng `await new Promise(...)`), nó vẫn gặp giới hạn về mặt ngữ cảnh. 
- Để chống Race Condition hoàn hảo trong hệ thống phân tán, cần có cơ chế Mutex nội tại hoặc Transaction của Database, thứ mà mô hình không thể tự import thư viện ngoài nếu không được prompt trước. Tuy vậy, mức độ giải quyết cú pháp của nó đã là tối đa so với một mô hình 1.5B.

---

## 3. Khắc phục vấn đề "Lặp code" (Repetition)
Nguyên nhân gốc rễ là ở khâu chuẩn bị Dataset JSONL, các cặp Prompt/Completion được đưa vào mà không có delimiter rõ ràng.

**Giải pháp:** 
- Đã bổ sung tham số `repetition_penalty = 1.1` vào hàm inference.
- Đã triển khai module `output_parser.py` ở Backend FastAPI để thực hiện hậu kiểm (Post-processing), cắt bỏ phần code thừa và chỉ trích xuất block code chính xác đầu tiên.

## 4. Kết luận
Mô hình **ThreadLearn-Qwen2.5-Coder-1.5B** thể hiện khả năng hiểu sâu sắc về kiến trúc bất đồng bộ và cơ chế Event Loop của Node.js. Chất lượng tái cấu trúc code của nó hoàn toàn đủ tiêu chuẩn để làm Core AI cho hệ thống tự động dò lỗi code của toàn bộ dự án.
