# Slide Nghiên Cứu — ThreadLearn AI

Outline slide phần "nghiên cứu" (research/background). Mỗi mục = 1 slide. Nội dung lấy từ `docs/RESEARCH_LOG.md`, `docs/reference-papers/`, `server/README.md` — không bịa số liệu.

---

## Slide 1 — Tiêu đề

- **ThreadLearn**: AI phát hiện & sửa lỗi Concurrency (Race Condition) trong JavaScript
- Tên nhóm, thành viên (Ân — AI1: dataset/fine-tune, Trung — AI2: serving/RAG/detector)
- Ngày báo cáo

---

## Slide 2 — Vấn đề thực tế (Motivation)

Nội dung nói:
- Node.js server dùng model **event loop đơn luồng**, không phải multi-thread như Java/C++ → lỗi concurrency có bản chất khác hẳn (không có deadlock, chủ yếu là atomicity/order violation).
- Lỗi race condition trong JS **khó phát hiện bằng mắt** — code trông tuần tự (nhất là với `async/await`) nhưng thực thi không đảm bảo thứ tự.
- Hậu quả nghiêm trọng trong thực tế (số liệu từ NodeCB, xem Slide 3): sai dữ liệu DB, crash, duplicate record.
- Công cụ hiện có (ESLint, TSan, Helgrind...) không phù hợp: TSan/Helgrind dùng cho C/C++ đa luồng thật, không áp dụng được cho event-loop; ESLint chỉ bắt lỗi cú pháp, không hiểu logic bất đồng bộ.
- → Cần công cụ **hiểu ngữ nghĩa async JS** + **AI hỗ trợ sửa tự động**, không chỉ cảnh báo.

---

## Slide 3 — Nghiên cứu nền tảng #1: NodeCB (ASE 2017)

*"A Comprehensive Study on Real World Concurrency Bugs in Node.js" — Wang et al.*

Trình bày (dùng số liệu thật từ bài):
- Khảo sát thực nghiệm đầu tiên về concurrency bug trong Node.js: 57 bug thật từ 53 project mã nguồn mở.
- **3 kiểu lỗi**: Atomicity Violation 65%, Order Violation 30%, Starvation 5% (không có Deadlock — khác hẳn hệ đa luồng truyền thống).
- **Nguyên nhân gốc**: API misuse chiếm 49% — dev tưởng API đồng bộ nhưng thực ra bất đồng bộ.
- **93% bug gây hậu quả nghiêm trọng** (crash, sai DB/file, treo).
- **77% bug KHÔNG sửa được bằng cách thêm synchronization/lock** (khác Java/C++) — cần sửa logic (bypass flag, atomic API, đổi thứ tự).
- **40% race xảy ra trên Database/File**, không chỉ shared memory trong RAM → công cụ detect hiện tại (chỉ check memory access) bỏ sót phần lớn.

→ Đây là **cơ sở thiết kế bộ pattern detect (paper trình bày 5 pattern chính, production code có 14 JS + 4 Python pattern)** trong `race_detector.py` của ThreadLearn (map trực tiếp từ finding của NodeCB).

---

## Slide 4 — Nghiên cứu nền tảng #2: PCWMs (arXiv 2026)

*"Learning Reasoning World Models for Parallel Code" — Singh et al., Lawrence Livermore National Lab*

Trình bày:
- Vấn đề: LLM viết code song song (parallel) kém hơn code tuần tự — ít dữ liệu train, thread interaction khó suy luận chỉ bằng đọc code.
- Cách cũ: gọi tool thật (ThreadSanitizer, Caliper) để check — nhưng tốn công compile, không dùng được cho code chưa hoàn chỉnh, chậm.
- Giải pháp: dạy LLM **tự mô phỏng kết quả tool** mà không cần chạy — gọi là "World Model".
- **Phát hiện quan trọng nhất**: dạy LLM suy luận theo kiểu **"tự đoán trước rồi giải thích" (A Priori CoT) THẤT BẠI HOÀN TOÀN** — accuracy rớt xuống 49.3%, mọi model đều collapse về đoán 1 nhãn cố định.
- **Giải pháp: Hindsight Chain-of-Thought** — cho model biết đáp án đúng (từ tool thật) TRƯỚC, rồi yêu cầu viết lý luận dẫn đến đáp án đó (forward reasoning, không nhắc "vì tôi biết..."). Kết quả tăng lên 73.0% avg.
- Race-fixing agent dùng World Model đạt fix rate cao hơn cả dùng thông tin gốc từ tool thật (74.7% vs 74.4%) — vì reasoning trace giàu ngữ nghĩa hơn output thô của tool.

→ ThreadLearn áp dụng **kỹ thuật Hindsight CoT tương tự** khi tạo dữ liệu train cho model fine-tune (dùng `race_detector.py` làm ground-truth, không để model tự đoán).

---

## Slide 5 — Khoảng trống nghiên cứu (Research Gap)

So sánh để làm rõ tại sao 2 bài trên **chưa đủ**, cần ThreadLearn:

| | NodeCB | PCWMs | ThreadLearn |
|---|---|---|---|
| Phạm vi | Khảo sát thực nghiệm (không xây tool) | C/C++ OpenMP, shared-memory | JavaScript event-loop |
| Output | Tìm hiểu bug pattern | Detect race (world model) | Detect **+ tự động fix** |
| Ngôn ngữ | — | C/C++ | JavaScript (Node.js) |
| Model | — | 7B–32B, full fine-tune, cần GPU cluster | 1.5B, QLoRA, chạy được trên GPU tiêu dùng (T4) |
| Kiến thức domain | — | Không có RAG | RAG (BM25 + knowledge base) bổ sung ngữ cảnh |

Kết luận gap: chưa có công cụ nào **kết hợp** static detection (rule-based, có căn cứ từ NodeCB) + fine-tuned LLM nhỏ gọn (học theo Hindsight CoT như PCWMs) + RAG để **fix code JavaScript tự động, triển khai được với tài nguyên hạn chế**.

---

## Slide 6 — Đóng góp của ThreadLearn (Contribution)

- Bộ race-condition detector cho JavaScript (14 pattern trong production code; paper trình bày 5 pattern chính — closure_loop_var, shared_var_settimeout, promise_no_await, concurrent_write_array, counter_no_atomic), xây từ taxonomy NodeCB (regex-based, không cần compile — hoạt động cả với code chưa hoàn chỉnh).
- Model fine-tune nhỏ (Qwen2.5-Coder-1.5B + QLoRA) học theo nguyên lý Hindsight CoT — triển khai local, không cần GPU cluster.
- Pipeline RAG (BM25 + knowledge base 2050 tài liệu JS concurrency pattern) tăng độ chính xác fix code.
- Kiến trúc fix **per-issue** (mỗi lỗi 1 lần gọi LLM riêng, có dedup + mở rộng ngữ cảnh) — giải quyết hạn chế model nhỏ không sửa tốt nhiều lỗi cùng lúc.
- Đã eval trên 30-case thực tế (bug thật từ npm package production) — không chỉ benchmark tổng hợp.

---

## Slide 7 — Workflow tổng quan của AI (phần Ân trình bày)

Sơ đồ flow (dùng ảnh vẽ bằng Gemini hoặc `docs/slide/workflow_prompt.txt`), diễn giải bằng lời:

**Input**: đoạn code JavaScript người dùng dán vào.

**Các bước xử lý tuần tự**:
1. **Race Detector** (`race_detector.py`) — quét code bằng bộ pattern regex tĩnh (closure loop var, shared var trong setTimeout, promise không await, counter không atomic, v.v. — paper highlight 5 pattern chính, production có 14 JS pattern). Không cần chạy code, không cần compile.
2. **Keyword Extraction** — rút từ khóa mô tả lỗi để tìm tài liệu liên quan, theo thứ tự ưu tiên: pattern semantic có sẵn → AST (dự phòng) → tokenize thường (dự phòng cuối).
3. **BM25 Retrieval** — tìm kiếm trong knowledge base 2050 tài liệu concurrency, lấy ra các đoạn giải thích + ví dụ fix liên quan nhất.
4. **Prompt Builder (RAG)** — ghép: code lỗi + issue detect được + tài liệu retrieved → 1 prompt hoàn chỉnh cho LLM.
5. **LLM Fix (per-issue)** — model Qwen2.5-Coder-1.5B (fine-tune QLoRA) sinh fix cho **từng issue riêng biệt** (không gộp chung 1 lần cho cả file).
6. **Streaming kết quả** — trả kết quả dần về giao diện qua SSE, không bắt người dùng chờ hết toàn bộ tiến trình mới thấy gì.

**Output**: danh sách issue (mức độ nghiêm trọng, dòng code liên quan, giải thích, code đã sửa) + tài liệu tham khảo.

---

## Slide 8 — Vì sao chọn từng kỹ thuật (tóm tắt, chi tiết xem `server/README.md`)

- **Regex-based detector thay vì AST-based**: nhanh, không cần parse cây cú pháp đầy đủ, đủ để bắt các pattern phổ biến theo NodeCB (14 JS pattern trong production). AST chỉ dùng dự phòng.
- **BM25 thay vì vector embedding**: nhẹ, không cần GPU, đủ tốt cho tài liệu ngắn có từ khóa kỹ thuật rõ ràng.
- **QLoRA thay vì full fine-tune**: giới hạn phần cứng (Kaggle T4 16GB) — so với PCWMs cần GPU cluster.
- **Per-issue LLM call thay vì 1 call/file**: model 1.5B nhỏ, không đủ khả năng sửa chính xác nhiều lỗi cùng lúc trong 1 lần sinh.
- **Redis cache theo hash code**: tránh gọi LLM lặp lại cho cùng 1 đoạn code.

---

## Ghi chú khi làm slide thật (PowerPoint/Canva/Genspark...)

- Slide 3, 4: nên trích trực tiếp bảng số liệu thật (đã có trong `docs/reference-papers/explain_nodecb.md`, `explain_pcwms.md`) thay vì diễn giải lại — tăng độ tin cậy học thuật.
- Slide 7: dùng hình flow đã tạo (xem prompt Gemini đã gửi trong hội thoại) — nên convert cả 6 bước pipeline thật (không chỉ workflow đơn giản) nếu slide dành cho báo cáo kỹ thuật sâu; dùng bản đơn giản nếu slide dành cho khán giả không chuyên.
- Trích dẫn nguồn: NodeCB (Wang et al., ASE 2017), PCWMs (Singh et al., arXiv 2604.20926v2, 2026, LLNL + Northeastern University) — ghi rõ trong slide cuối "Tài liệu tham khảo".
