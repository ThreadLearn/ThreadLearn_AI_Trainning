# Dịch đoạn tài liệu: Tập dữ liệu (Dataset)

Nghiên cứu của chúng tôi sử dụng ba tập dữ liệu riêng biệt, mỗi tập đóng một vai trò khác nhau trong hệ thống.

**Tập dữ liệu tinh chỉnh (Fine-tuning dataset).**
Tập dữ liệu tinh chỉnh bao gồm 783 mẫu định dạng JSONL có cấu trúc `(code, detector_output, reasoning_trace, fix)`, trong đó mỗi "chuỗi suy luận" (reasoning trace) được viết bởi một mô hình giáo viên (teacher model) sau khi đã biết trước cách sửa lỗi chính xác (hindsight Chain-of-Thought).
Các loại lỗi bao trùm toàn bộ 10 danh mục trong bộ đánh giá thực tế (real-world benchmark), cùng với các biến thể tổng hợp (synthetic) bổ sung nhằm cân bằng các danh mục lỗi hiếm gặp (như Zalgo, Rò rỉ Stream, Callback Hell).

**Cơ sở tri thức (Knowledge base).**
Cơ sở tri thức phục vụ cho quá trình truy xuất (retrieval) chứa 2.050 tài liệu JavaScript được thu thập từ các nguồn uy tín: MDN Web Docs (99 tài liệu bao gồm `Promise`, `async`/`await`, và hành vi API của Node.js), tài liệu thư viện chính thức bao gồm RxJS, p-limit, async-mutex, và Bluebird (50 tài liệu), các mô tả pattern được ThreadLearn tuyển chọn (151 tài liệu), và 1.750 tài liệu tổng hợp được tạo ra thông qua hoán vị ngữ cảnh từ tập tài liệu tuyển chọn nhằm cải thiện độ bao phủ của thuật toán BM25 trên các biến thể tên API khác nhau.
Toàn bộ 2.050 tài liệu đều viết bằng JavaScript và được chia thành ba nhóm: `patterns` (1.418), `race-conditions` (352), và `anti-patterns` (280).

**Bộ đánh giá thực tế (Real-world evaluation benchmark).**
Để tránh thiên kiến đánh giá (evaluation bias) phát sinh từ các bài kiểm tra do hệ thống tự sinh ra, chúng tôi đã xây dựng một bộ đánh giá gồm 30 lỗi bất đồng bộ (concurrency bugs) JavaScript trong thực tế, được trích xuất hoàn toàn từ các mã nguồn thư viện (package) production mở.
Mỗi trường hợp đều được truy vết nguồn gốc từ một issue cụ thể trên GitHub hoặc từ việc sử dụng sai API đã được ghi nhận trong các thư viện bao gồm: `request`, `mysql`, `async`, `pg`, `passport`, `ioredis`, `express`, `mongoose`, `bull`, `sequelize`, và nhiều thư viện khác.
Dưới đây là tóm tắt sự phân bổ qua 10 danh mục lỗi (30 trường hợp từ các gói npm production):

| Danh mục lỗi (Category) | Số lượng | Ví dụ các package bị lỗi |
|---|---|---|
| Race Condition | 5 | `request`, `passport`, `bull` |
| Double Callback | 4 | `mysql`, `ioredis`, `async` |
| Unhandled Rejection | 5 | `express`, `mongoose`, `co` |
| Resource Exhaustion | 4 | `pg`, `axios`, `sequelize` |
| Event Loop Blocking | 3 | `express` (sync middleware), Node.js crypto |
| Sequential Awaits | 3 | `express-session`, Node.js best practices |
| Zalgo | 2 | `async` |
| Context Loss | 2 | `express-async-errors`, Node.js timers |
| Stream Leak | 1 | Node.js streams |
| Callback Hell | 1 | `async` |
| **Tổng cộng** | **30** | |

Tất cả các bug này đều bắt nguồn từ các trang theo dõi lỗi (issue tracker) chính thức trên GitHub hoặc tài liệu của Node.js, chứ không phải là các kịch bản do chúng tôi tự bịa ra (synthetic).
Thiết kế bộ đánh giá này giúp loại bỏ rủi ro tạo ra các bài kiểm tra có lợi cho mô hình (model-favorable test cases), điều thường xảy ra khi cùng một hệ thống vừa tạo dữ liệu huấn luyện lại vừa tự tạo ra dữ liệu để đánh giá chính nó.
 
