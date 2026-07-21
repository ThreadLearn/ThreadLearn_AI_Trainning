# Slide Text (EN) + Speaker Notes (VI)

Mỗi slide: **phần chữ lên slide** (tiếng Anh, ngắn, gạch đầu dòng) + **nội dung nói** (tiếng Việt, đầy đủ). Đọc kèm `01_research_slides.md` để biết cấu trúc tổng.

---

## Slide 1 — Title

**Slide text:**
```
ThreadLearn
AI-Powered Race Condition Detection & Auto-Fix for JavaScript

[Team names] — AI1: Dataset & Fine-tuning | AI2: RAG Pipeline & Serving
[Date]
```

**Nói (VN):**
Giới thiệu tên đề tài: ThreadLearn — hệ thống AI phát hiện và tự động sửa lỗi race condition (lỗi tương tranh) trong code JavaScript. Giới thiệu nhanh 2 mảng: một bạn phụ trách thu thập dữ liệu và fine-tune model, một bạn phụ trách pipeline RAG và phần serving/API.

---

## Slide 2 — Problem Statement

**Slide text:**
```
Why This Matters

- Node.js: single-threaded event loop — different from Java/C++ multithreading
- Async bugs are invisible by reading code, especially with async/await
- No deadlocks, but atomicity & order violations are common
- Existing tools don't fit:
  • ThreadSanitizer / Helgrind → built for real multithreading, not event loop
  • ESLint → syntax only, no async-logic understanding
```

**Nói (VN):**
Node.js chạy trên mô hình event loop đơn luồng, hoàn toàn khác cơ chế đa luồng của Java hay C++. Vì vậy các lỗi liên quan đến tính đồng thời trong JavaScript có bản chất khác — không có deadlock nhưng lại có nhiều lỗi về thứ tự thực thi và tính nguyên tử. Cái khó là những lỗi này không nhìn thấy được chỉ bằng mắt đọc code, đặc biệt là với async/await — code trông có vẻ chạy tuần tự nhưng thực tế thứ tự thực thi không được đảm bảo. Công cụ hiện có như ThreadSanitizer, Helgrind được thiết kế cho hệ đa luồng thực sự (C/C++), không áp dụng được cho event loop của Node.js. Còn ESLint thì chỉ kiểm tra cú pháp, không hiểu được logic bất đồng bộ. Đây chính là khoảng trống cần giải quyết.

---

## Slide 3 — Related Work #1: NodeCB (ASE 2017)

**Slide text:**
```
NodeCB — Wang et al., ASE 2017
"A Comprehensive Study on Real World Concurrency Bugs in Node.js"

- First large-scale empirical study: 57 real bugs, 53 open-source projects
- Bug types: Atomicity Violation 65% | Order Violation 30% | Starvation 5%
  (No deadlocks — unlike traditional multithreaded systems)
- Root cause: API misuse — 49%
- 93% of bugs cause serious consequences (crash, data corruption)
- 77% of bugs CANNOT be fixed by adding synchronization/locks
- 40% of races happen on Database/File, not just in-memory variables
```

**Nói (VN):**
Đây là nghiên cứu thực nghiệm đầu tiên và toàn diện nhất về lỗi concurrency trong Node.js, thu thập 57 lỗi thật từ 53 dự án mã nguồn mở trên GitHub. Kết quả cho thấy 3 loại lỗi chính: vi phạm tính nguyên tử chiếm 65% — tức là chuỗi đọc-sửa-ghi bị một callback khác chen vào giữa; vi phạm thứ tự chiếm 30% — code giả định việc A xong trước việc B nhưng không có gì đảm bảo điều đó; và starvation chỉ chiếm 5%. Đáng chú ý là không hề có deadlock, khác hẳn với hệ đa luồng truyền thống. Về nguyên nhân, gần một nửa số lỗi — 49% — đến từ việc lập trình viên hiểu sai cách hoạt động của API, tưởng nó đồng bộ nhưng thực ra là bất đồng bộ. 93% số lỗi gây hậu quả nghiêm trọng như crash, sai dữ liệu. Và điều quan trọng nhất cho hướng đi của nhóm: 77% số lỗi này KHÔNG thể sửa bằng cách thêm khóa đồng bộ như trong Java hay C++, mà phải sửa bằng cách thay đổi logic. Ngoài ra 40% lỗi race xảy ra trên database và file, không chỉ trên biến trong bộ nhớ — điều mà các công cụ phát hiện hiện tại thường bỏ sót. Đây chính là cơ sở để nhóm xây dựng bộ pattern phát hiện lỗi trong race_detector.py (14 JS pattern trong production; paper trình bày 5 pattern chính).

---

## Slide 4 — Related Work #2: PCWMs (arXiv 2026)

**Slide text:**
```
PCWMs — Singh et al., LLNL + Northeastern University, 2026
"Learning Reasoning World Models for Parallel Code"

- Problem: LLMs are weak at parallel code — hard to reason without running it
- Idea: train LLM to simulate analysis tools (World Model) — no compile/run needed
- Key finding: "guess-then-explain" reasoning (A Priori CoT) COLLAPSES → 49.3% accuracy
- Solution: Hindsight Chain-of-Thought
  → give model the correct answer FIRST, then generate reasoning that leads to it
  → accuracy: 49.3% (failed) → 73.0% (Hindsight CoT)
- Reasoning-rich feedback beats raw tool output (74.7% vs 74.4% fix rate)
```

**Nói (VN):**
Bài báo này giải quyết vấn đề: các mô hình ngôn ngữ lớn viết code song song rất kém, vì thread interaction rất khó suy luận chỉ bằng cách đọc code. Cách làm truyền thống là để LLM gọi công cụ thật như ThreadSanitizer để kiểm tra, nhưng tốn công compile và chậm. Nhóm tác giả đề xuất huấn luyện LLM để tự mô phỏng kết quả của công cụ đó — gọi là World Model — không cần biên dịch hay chạy thật. Phát hiện quan trọng nhất của bài báo là: nếu để model tự đoán kết quả trước rồi mới giải thích — gọi là A Priori Chain-of-Thought — thì toàn bộ các model đều sụp đổ, độ chính xác chỉ còn 49.3%, tức là gần như đoán bừa. Giải pháp là kỹ thuật Hindsight Chain-of-Thought: cho model biết đáp án đúng từ công cụ thật trước, rồi yêu cầu nó viết lý luận dẫn đến đáp án đó theo chiều thuận — từ code suy ra kết luận, không được nói kiểu "vì tôi biết đáp án nên...". Cách này giúp độ chính xác tăng vọt lên 73%. Một phát hiện thú vị khác: khi dùng model này để tự động sửa lỗi, kết quả sửa còn tốt hơn cả khi dùng thông tin gốc trực tiếp từ công cụ — vì lý luận có ngữ cảnh phong phú hơn giúp model sửa chính xác hơn. Nhóm áp dụng đúng nguyên lý Hindsight CoT này khi tạo dữ liệu huấn luyện cho model của mình.

---

## Slide 5 — Research Gap

**Slide text:**
```
What's Missing

              NodeCB          PCWMs              ThreadLearn
Scope         Empirical study  C/C++ OpenMP       JavaScript event loop
Output        Bug taxonomy     Detect only        Detect + Auto-Fix
Model size    —                7B–32B, GPU cluster 1.5B, QLoRA, consumer GPU
Domain input  —                No RAG             RAG (BM25 + knowledge base)

Gap: no tool combines rule-based JS detection + small fine-tuned LLM
     + RAG in a deployable package
```

**Nói (VN):**
So sánh hai hướng nghiên cứu nền tảng cho thấy khoảng trống rõ ràng. NodeCB chỉ là một nghiên cứu khảo sát, không xây dựng công cụ nào cả. PCWMs xây được công cụ nhưng chỉ áp dụng cho C/C++ với OpenMP, chỉ dừng ở việc phát hiện lỗi chứ chưa tự động sửa, và cần model rất lớn từ 7 đến 32 tỷ tham số chạy trên cụm GPU chuyên dụng, không có RAG để bổ sung kiến thức domain. Trong khi đó, JavaScript có mô hình concurrency hoàn toàn khác C/C++, chưa có nghiên cứu nào áp dụng những kỹ thuật này cho JS. Đây chính là khoảng trống: chưa có công cụ nào kết hợp được cả phát hiện lỗi dựa trên rule cho JavaScript, model fine-tune nhỏ gọn triển khai được với tài nguyên hạn chế, và RAG để bổ sung ngữ cảnh — tất cả trong một pipeline hoàn chỉnh từ phát hiện đến tự động sửa.

---

## Slide 6 — Our Contribution

**Slide text:**
```
ThreadLearn Contributions

- Static race detector for JavaScript (5 core patterns highlighted in the paper; 14 patterns in production code), built from NodeCB taxonomy
- Fine-tuned Qwen2.5-Coder-1.5B (QLoRA) — deployable on a single consumer GPU
- RAG pipeline: BM25 + 2,050-document JS concurrency knowledge base
- Per-issue LLM fixing — accurate even when multiple bugs exist in one file
- Evaluated on 30 real-world bugs from production npm packages
```

**Nói (VN):**
Đóng góp của nhóm gồm 5 điểm chính. Thứ nhất, bộ pattern phát hiện lỗi race condition tĩnh cho JavaScript (paper trình bày 5 pattern chính; production code có 14 pattern), được xây dựng trực tiếp từ phân loại lỗi trong nghiên cứu NodeCB. Thứ hai, model Qwen2.5-Coder 1.5B được fine-tune bằng kỹ thuật QLoRA, có thể triển khai trên một GPU phổ thông thay vì cần cụm GPU lớn. Thứ ba, pipeline RAG kết hợp BM25 tìm kiếm trong kho tri thức 2050 tài liệu về các pattern concurrency trong JavaScript. Thứ tư, cơ chế sửa lỗi theo từng issue riêng biệt — giải quyết vấn đề model nhỏ không đủ khả năng sửa chính xác nhiều lỗi cùng lúc trong một file. Cuối cùng, hệ thống đã được đánh giá trên 30 lỗi thực tế lấy từ các package npm production, không chỉ là benchmark tổng hợp.

---

## Slide 7 — AI Workflow (Ân trình bày)

**Slide text:**
```
End-to-End Pipeline

Input: JavaScript code snippet
   ↓
1. Race Detector — 10 static regex patterns, no compile needed
   ↓
2. Keyword Extraction — semantic patterns → AST fallback → tokenize fallback
   ↓
3. BM25 Retrieval — search 2,050-doc knowledge base
   ↓
4. Prompt Builder (RAG) — merge code + issue + retrieved docs
   ↓
5. Per-Issue LLM Fix — fine-tuned Qwen2.5-Coder-1.5B, one call per issue
   ↓
6. Streaming Results — issues appear progressively via SSE
   ↓
Output: Issue list (severity, line, explanation, fixed code) + references
```

**Nói (VN):**
Đây là toàn bộ pipeline xử lý một lần phân tích, từ đầu vào đến đầu ra. Đầu vào là một đoạn code JavaScript người dùng dán vào. Bước một, Race Detector quét code bằng bộ pattern regex tĩnh — không cần biên dịch hay chạy code, hoạt động được cả với code chưa hoàn chỉnh. Bước hai, hệ thống trích xuất từ khóa mô tả lỗi theo thứ tự ưu tiên: ưu tiên các pattern ngữ nghĩa có sẵn trước, nếu không khớp thì dùng AST làm dự phòng, cuối cùng mới dùng tokenize thông thường. Bước ba, dùng BM25 tìm kiếm trong kho tri thức 2050 tài liệu để lấy ra các đoạn giải thích và ví dụ sửa lỗi liên quan nhất. Bước bốn, ghép code lỗi, issue phát hiện được, và tài liệu tìm được thành một prompt hoàn chỉnh — đây chính là kỹ thuật RAG. Bước năm, model Qwen2.5-Coder đã fine-tune sẽ sinh fix cho từng issue riêng biệt, không gộp chung một lần cho cả file, để đảm bảo độ chính xác. Bước sáu, kết quả được trả về dần theo từng issue qua streaming, người dùng không phải chờ toàn bộ quá trình xong mới thấy kết quả. Đầu ra cuối cùng là danh sách các issue kèm mức độ nghiêm trọng, vị trí dòng code, giải thích, code đã sửa, và tài liệu tham khảo.

---

## Slide 8 — Why These Techniques

**Slide text:**
```
Design Choices

- Regex-based detector (not full AST) — fast, works on incomplete code
- BM25 (not vector embeddings) — lightweight, no GPU needed for retrieval
- QLoRA (not full fine-tuning) — fits a single 16GB GPU (Kaggle T4)
- Per-issue LLM calls (not one call per file) — small model, higher accuracy
- Redis cache by code hash — avoids redundant LLM calls
```

**Nói (VN):**
Slide này giải thích ngắn gọn lý do chọn từng kỹ thuật, chi tiết đầy đủ hơn có trong tài liệu README của nhóm. Chọn detector dựa trên regex thay vì phân tích AST đầy đủ vì nó nhanh và hoạt động được ngay cả khi code chưa hoàn chỉnh, chưa parse được thành cây cú pháp hợp lệ. Chọn BM25 thay vì vector embedding vì nó nhẹ, không cần GPU cho việc tìm kiếm, và đủ hiệu quả với tài liệu kỹ thuật có từ khóa rõ ràng. Chọn QLoRA thay vì fine-tune toàn bộ model vì giới hạn phần cứng — chỉ có GPU Kaggle T4 16GB, so với PCWMs cần cả cụm GPU. Chọn gọi LLM riêng cho từng issue thay vì gộp chung một lần cho cả file, vì model 1.5B tham số khá nhỏ, không đủ khả năng xử lý chính xác nhiều lỗi cùng lúc trong một lần sinh. Cuối cùng, dùng Redis cache theo hash của code để tránh gọi lại LLM cho cùng một đoạn code đã phân tích trước đó.

---

## Slide 9 — References (nên có, không có trong outline gốc)

**Slide text:**
```
References

[1] Wang, K., et al. "A Comprehensive Study on Real World Concurrency
    Bugs in Node.js." ASE 2017.

[2] Singh, et al. "Learning Reasoning World Models for Parallel Code."
    arXiv:2604.20926v2, 2026. Lawrence Livermore National Laboratory
    & Northeastern University.
```

**Nói (VN):**
Đây là hai nguồn tài liệu tham khảo chính mà nhóm dựa vào để thiết kế hệ thống — một nghiên cứu khảo sát về lỗi thực tế trong Node.js, và một nghiên cứu về kỹ thuật huấn luyện model học lý luận cho code song song.
