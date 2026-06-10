# ThreadLearn: Outline Bài Báo Nghiên Cứu (Tiếng Việt)

**Đóng góp một câu:**
> ThreadLearn kết hợp phát hiện race condition tĩnh dựa trên quy tắc với mô hình Qwen2.5-Coder-1.5B được fine-tune bằng Hindsight CoT để vừa phát hiện vừa sửa lỗi concurrency trong JavaScript và Python, cải thiện F1 phát hiện X% và tỷ lệ chấp nhận bản sửa Y% so với baseline chỉ dùng quy tắc và baseline chỉ dùng LLM.

**Venue mục tiêu:** ASPLOS 2027 hoặc ICLR 2026 — 11–12 trang

---

## Tóm tắt (150–250 từ, 5 câu)

| Câu | Nội dung |
|-----|----------|
| S1 | Lỗi concurrency trong code async/đa luồng gây ra các sự cố nghiêm trọng trên môi trường production, trong khi các công cụ phát hiện tĩnh có tỷ lệ false positive cao và LLM thiếu khả năng suy luận đáng tin cậy về tương tác luồng. |
| S2 | Bộ phát hiện dựa trên quy tắc (NodeCB) bỏ sót các pattern phức tạp; phương pháp chỉ dùng LLM (PCWMs) chỉ đạt 75% độ chính xác khi phát hiện race mà không có phân tích cấu trúc rõ ràng. |
| S3 | ThreadLearn kết hợp bộ phát hiện tĩnh 10 pattern với mô hình Qwen2.5-Coder-1.5B được fine-tune bằng QLoRA trên các trace Hindsight Chain-of-Thought được căn bản hóa từ đầu ra của phân tích tĩnh. |
| S4 | Trên [benchmark], ThreadLearn phát hiện race với F1=X% (+Y% so với baseline NodeCB) và tạo bản sửa được chấp nhận trong Z% trường hợp (+W% so với baseline PCWM). |
| S5 | ThreadLearn là mã nguồn mở tại [repo]; bộ dữ liệu fine-tune và harness đánh giá được công khai. |

---

## S1. Giới thiệu (1.5–2 trang)

### §1.1 Phát biểu vấn đề (0.5 trang)

| Điểm | Nội dung |
|------|----------|
| Bối cảnh | JS async và Python đa luồng phổ biến trong backend web |
| Dẫn chứng NodeCB | 57 bug thực tế → 65% vi phạm tính nguyên tử, 30% vi phạm thứ tự |
| Mức độ tác động | 93% bug gây ra lỗi nghiêm trọng: crash, sai trạng thái DB, treo |
| Khoảng trống | Công cụ hiện tại: dựa trên quy tắc (FP cao) hoặc LLM (không đáng tin) |

### §1.2 Phân tích khoảng trống (0.5 trang)

| # | Khoảng trống |
|---|-------------|
| G1 | Bộ phát hiện dựa trên quy tắc không sửa được lỗi, chỉ phát hiện |
| G2 | LLM-only (PCWMs) đạt 75.2% nhưng cần 27K mẫu và không khai thác cấu trúc tĩnh |
| G3 | Không có hệ thống nào kết hợp phân tích tĩnh làm căn bản cho suy luận LLM |
| G4 | Thiếu pipeline end-to-end từ phát hiện → giải thích → sửa cho cả JS lẫn Python |

### §1.3 Insight chính (1 đoạn)

> *ThreadLearn phù hợp hơn cho việc xử lý lỗi concurrency trong codebase JS/Python production bằng cách sử dụng đầu ra của bộ phát hiện tĩnh làm tín hiệu căn bản cho việc fine-tune Hindsight CoT.*

### §1.4 Đóng góp (0.5 trang)

| # | Đóng góp | Section |
|---|---------|---------|
| 1 | **`race_detector`**: Bộ phân tích tĩnh 10 pattern cho JS + Python, tích hợp AST preprocessor | §3.2 |
| 2 | **Bộ dữ liệu Hindsight CoT**: Dataset tổng hợp được căn bản từ đầu ra detector tĩnh, fine-tune Qwen2.5-Coder-1.5B với QLoRA | §3.3 |
| 3 | **Pipeline ThreadLearn**: phát hiện → định dạng → sửa có RAG-augmented qua LLM fine-tuned | §3.4 |
| 4 | **Đánh giá**: So sánh với baseline NodeCB và baseline PCWM trên 3 metric | §5 |

**Hình 1** (trang 1): Sơ đồ tổng quan hệ thống — đầu vào code → AST preprocessor → race detector → report formatter → RAG pipeline → LLM fine-tuned → đầu ra bản sửa.

---

## S2. Nền tảng & Động lực (1–1.5 trang)

### §2.1 Phân loại lỗi Concurrency (0.5 trang)

| Loại lỗi | Tỷ lệ (NodeCB) | Ví dụ |
|----------|---------------|-------|
| Vi phạm tính nguyên tử | 65% | Hai lần gọi DB xen kẽ, mất cập nhật |
| Vi phạm thứ tự | 30% | Upload trước khi create hoàn thành |
| Starvation | 5% | setImmediate bị đói do hàng đợi I/O |
| `var i` trong vòng lặp + setTimeout | JS pattern | Closure bắt giá trị sai |
| Global var không Lock trong thread | Python pattern | Race trên biến chia sẻ |

### §2.2 Hạn chế của các phương pháp hiện tại (0.5 trang)

| Phương pháp | Hạn chế |
|------------|---------|
| Nghiên cứu NodeCB | Phát hiện dựa trên regex → FP cao, không sửa |
| PCWMs | 75.2% độ chính xác nhưng không dùng cấu trúc tĩnh, cần model lớn (7B–32B) |
| **Quan sát O1** | Đầu ra detector tĩnh (line range, pattern ID) cung cấp căn bản nhân quả mà suy luận LLM thiếu |
| **Quan sát O2** | Model nhỏ (1.5B) fine-tune với CoT có căn bản vượt model lớn với CoT generic |

### §2.3 Nền tảng AST Preprocessing (0.5 trang)

| Hàm | Chức năng | Ghi chú |
|-----|----------|---------|
| `stripComments` | Loại bỏ comments và docstrings | Python: `ast.unparse` (chính xác); JS: regex fallback |
| `normalizeWhitespace` | Chuẩn hóa khoảng trắng | Python: `ast.unparse`; JS: regex |
| `extractFunctions` | Trích xuất danh sách function/class | JS: không bắt arrow function — hạn chế |
| `extract_keywords` | Trích top-20 token identifier | Dùng cho RAG retrieval |

---

## S3. Thiết kế (3–4 trang)

**Hình 2**: Kiến trúc component — 5 module với mũi tên luồng dữ liệu

### §3.1 Tổng quan Kiến trúc Hệ thống (0.5 trang)

| Component | Vai trò |
|-----------|---------|
| `ast_preprocessor` | Làm sạch và chuẩn hóa code đầu vào |
| `race_detector` | Phát hiện 10 pattern race condition |
| `report_formatter` | Map pattern_id → severity + template sửa |
| `rag_pipeline` | Truy xuất ví dụ tương tự, augment LLM prompt |
| LLM fine-tuned | Tạo bản sửa có suy luận |
| FastAPI server | Expose endpoint `/analyze` |

### §3.2 Bộ Phát Hiện Race Tĩnh (1 trang)

| Nhóm Pattern | Pattern ID | Ngôn ngữ |
|-------------|-----------|---------|
| Closure/async | `closure_loop_var`, `shared_var_settimeout`, `promise_no_await` | JS |
| Trạng thái chia sẻ | `concurrent_write_array`, `counter_no_atomic` | JS |
| An toàn luồng | `global_var_thread`, `shared_list_no_lock`, `thread_read_write_race` | Python |
| Vòng đời | `missing_join`, `singleton_lazy_init` | Python |

| Tính năng | Mô tả |
|----------|-------|
| Triệt tiêu FP | Phát hiện Lock → bỏ qua flag shared_list/thread_read_write/singleton |
| TypeScript | Xử lý như JavaScript |
| Đầu ra | `{pattern_id, line_range, description}` |
| Phương án bị loại | Phát hiện JS dựa trên AST (bị loại — cần Node.js runtime) |

### §3.3 Fine-tune Hindsight CoT (1 trang)

| Thành phần | Chi tiết |
|-----------|---------|
| Cảm hứng | PCWMs: teacher model viết trace suy luận biết trước kết quả |
| Tuple training | `(code, đầu ra detector tĩnh, trace CoT, bản sửa)` |
| Model | Qwen2.5-Coder-1.5B |
| Phương pháp | QLoRA: r=16, alpha=32, quantization 4-bit NF4 |
| Framework | SFTTrainer (trl≥1.5.0) — không gọi `get_peft_model()` thủ công |
| Phương án bị loại | Full fine-tune (quá tốn compute); RAG-only (không có suy luận) |

### §3.4 Pipeline Sửa Lỗi RAG-Augmented (0.5 trang)

| Bước | Mô tả |
|------|-------|
| 1. Embed | Nhúng code đầu vào thành vector |
| 2. Retrieve | Tìm ví dụ đã sửa tương tự từ kho RAG |
| 3. Format | `report_formatter` map pattern_id → mức độ nghiêm trọng + template sửa |
| 4. Generate | LLM fine-tuned + RAG context → bản sửa cuối |

### §3.5 Phương Án Thiết Kế Bị Loại (0.5 trang)

| Phương án | Lý do bị loại |
|----------|--------------|
| Chỉ dùng LLM để phát hiện | FP cao, không có attribution theo dòng |
| Chỉ dùng tĩnh | Phát hiện được nhưng không sửa |
| Model lớn (7B+) | Không thực tế khi triển khai local |

---

## S4. Triển khai (0.5–1 trang)

| Mục | Chi tiết |
|-----|---------|
| Ngôn ngữ & Framework | Python 3.10+, FastAPI |
| Tổng LOC | ~1,200 LOC |
| `race_detector.py` | 320 LOC, 10 detector, quét O(n) |
| Model adapter | LoRA SafeTensors tại `./threadlearn-qwen2.5-coder-1.5b/final_adapter` |
| Hạ tầng | Docker: Redis cache (localhost:6379), Atlas MongoDB |
| Kiểm soát đồng thời | Semaphore trong server |
| Quyết định kỹ thuật | Fallback graceful nếu import `ast_preprocessor` thất bại (CI isolation) |

---

## S5. Đánh giá (3–4 trang)

### §5.1 Thiết lập Thực nghiệm (0.5 trang)

| Hạng mục | Chi tiết |
|---------|---------|
| Baseline 1 | Chỉ dùng quy tắc kiểu NodeCB |
| Baseline 2 | Chỉ dùng LLM kiểu PCWM (Qwen2.5-Coder-1.5B không fine-tune) |
| Hệ thống của chúng tôi | ThreadLearn (tĩnh + LLM fine-tuned) |
| Bộ dữ liệu | 20 test case tổng hợp + [bộ dữ liệu thực tế TBD] |
| Metric | Detection F1, False Positive Rate, Fix Acceptance Rate, Latency (ms/request) |

**Bảng 1**: Kết quả phát hiện — Phương pháp × (Precision / Recall / F1 / FPR)

### §5.2 So sánh Phát Hiện End-to-End (1 trang)

| So sánh | Giả thuyết |
|--------|-----------|
| ThreadLearn vs chỉ-quy tắc | Cải thiện F1 trên pattern phức tạp (vi phạm thứ tự, API misuse) |
| ThreadLearn vs chỉ-LLM | Cải thiện F1 với CoT có căn bản vs suy luận generic |

**Hình 3**: Biểu đồ cột F1 — 3 phương pháp × phân tách JS/Python

### §5.3 Đánh giá Chất lượng Sửa Lỗi (1 trang)

| Metric | Phương pháp đo |
|--------|--------------|
| Fix Acceptance Rate | Đánh giá người dùng hoặc compile + test pass |
| Case study 1 | `var i` closure → sửa thành `let i` |
| Case study 2 | Global var trong thread → thêm Lock |
| So sánh | PCWM gốc: +2.7%–11.1% với world model feedback |

**Hình 4**: Tỷ lệ chấp nhận bản sửa — ThreadLearn vs chỉ-LLM vs chỉ-quy tắc (không có fix)

### §5.4 Ablation Study (1 trang)

| Thành phần bị loại | Tác động dự kiến |
|------------------|----------------|
| Loại bỏ căn bản tĩnh | F1 giảm X% |
| Loại bỏ RAG | Chất lượng sửa giảm Y% |
| Loại bỏ Hindsight CoT | Độ chính xác giảm Z% (xác nhận kết quả PCWMs) |
| QLoRA r=8 vs r=16 | Đánh đổi độ chính xác vs bộ nhớ |

**Bảng 2**: Ablation — Component × Metric

### §5.5 Khả năng Mở Rộng & Độ Trễ (0.5 trang)

| Metric | Nguồn |
|--------|-------|
| Requests/giây | Kết quả Locust load test |
| P95 latency | Locust load test |
| Ảnh hưởng Semaphore | Tác động đến throughput |

---

## S6. Công trình Liên quan (1 trang)

| Nhóm | Công trình tiêu biểu | Điểm khác biệt của ThreadLearn |
|------|---------------------|-------------------------------|
| Công cụ phát hiện tĩnh | ThreadSanitizer, Helgrind, ESLint async rules | Phát hiện không sửa, không có suy luận LLM |
| Nghiên cứu bug thực nghiệm | NodeCB (Wang et al. 2017), bug concurrency Android | Nguồn taxonomy, không cung cấp sửa tự động |
| LLM cho phân tích code | PCWMs (Singh et al. 2026), CodeBERT, CodeT5 | Chỉ dùng LLM, không khai thác cấu trúc tĩnh |
| Fine-tuning cho code | QLoRA, SFT on code, PEFT | Phương pháp training, không nhắm đến race detection |

**Bảng 3** (tùy chọn): Ma trận so sánh — Phương pháp × (Phát hiện / Sửa / JS / Python / Fine-tuned)

---

## S7. Kết luận (0.5 trang)

| Câu | Nội dung |
|-----|----------|
| S1 | Lỗi concurrency vẫn là nguyên nhân hàng đầu gây sự cố production trong ứng dụng async và đa luồng, nhưng chưa có công cụ nào vừa phát hiện vừa sửa chúng một cách đáng tin cậy. |
| S2 | ThreadLearn kết hợp bộ phát hiện race tĩnh 10 pattern với mô hình Qwen2.5-Coder-1.5B fine-tune bằng Hindsight CoT để cung cấp pipeline phát hiện và tạo bản sửa end-to-end cho JavaScript và Python. |
| S3 | ThreadLearn đạt F1=X% khi phát hiện race (+Y% so với NodeCB) và tỷ lệ chấp nhận bản sửa Z% (+W% so với baseline PCWMs), chứng minh rằng căn bản tĩnh cải thiện đáng kể khả năng suy luận concurrency của LLM. |

**Công việc tương lai:** Mở rộng sang TypeScript AST (thay regex), thêm pattern MPI/CUDA, phân tích đa file đa ngôn ngữ.

---

## Tóm tắt Hình & Bảng

| # | Loại | Section | Nội dung |
|---|------|---------|---------|
| Hình 1 | Sơ đồ hệ thống | Giới thiệu | Tổng quan pipeline end-to-end |
| Hình 2 | Kiến trúc | Thiết kế | Luồng dữ liệu 5 component |
| Hình 3 | Biểu đồ cột | Đánh giá §5.2 | F1 — 3 phương pháp × JS/Python |
| Hình 4 | Biểu đồ cột | Đánh giá §5.3 | Tỷ lệ chấp nhận bản sửa |
| Bảng 1 | Kết quả | Đánh giá §5.2 | Precision/Recall/F1/FPR |
| Bảng 2 | Ablation | Đánh giá §5.4 | Đóng góp từng component |
| Bảng 3 | So sánh | Công trình liên quan | Phương pháp × tính năng |

---

## Trạng thái Dữ liệu Thực nghiệm

| Hạng mục | Trạng thái |
|---------|-----------|
| Fine-tune model | Chưa chạy (AI1-07 blocked — cần GPU) → F1 TBD |
| Bộ dữ liệu thực tế | Chưa chọn |
| Load test | AI2-10 chưa hoàn chỉnh |
| 20 test case tổng hợp | Hoàn thành ✅ (`test_race_detector.py`) |
