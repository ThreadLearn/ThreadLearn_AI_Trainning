# ThreadLearn: Mô hình ngôn ngữ tinh chỉnh kết hợp tăng cường truy xuất để phát hiện và khắc phục lỗi đồng thời trong JavaScript

**Tác giả:** Lê Trí Trung[1], Hà Văn Ân[2]
**Cơ quan:** [1, 2] Đại học FPT, Đà Nẵng, Việt Nam

## Tóm tắt (Abstract)
Lỗi đồng thời (Concurrency bugs) trong mã JavaScript bất đồng bộ (Node.js) là nguyên nhân hàng đầu gây ra các sự cố nghiêm trọng trong các hệ thống sản phẩm (production systems), bao gồm lỗi chạy đua dữ liệu (data races), mất bản cập nhật (lost updates) và treo ứng dụng. Các công cụ hiện tại được chia thành hai loại: công cụ dò tĩnh dựa trên quy tắc (rule-based static detectors) có thể xác định các mẫu đáng ngờ nhưng không thể tạo ra bản sửa lỗi, và các mô hình ngôn ngữ lớn (LLMs) có khả năng lập luận về mã nhưng lại dễ bỏ sót dòng gây lỗi và đòi hỏi mô hình kích thước lớn (7B-32B tham số) để hoạt động hiệu quả. 
ThreadLearn giải quyết cả hai điểm yếu này bằng cách kết hợp một công cụ dò lỗi chạy đua tĩnh (static race detector) gồm 5 mẫu với một mô hình ngôn ngữ nhỏ (Qwen2.5-Coder-1.5B) được tinh chỉnh bằng QLoRA trên 783 ví dụ đào tạo đi kèm suy luận dạng Chuỗi tư duy nhận thức muộn (hindsight Chain-of-Thought). Tại thời điểm suy luận (inference time), một đường ống truy xuất BM25 (BM25 retrieval pipeline) sẽ tìm nạp 3 tài liệu liên quan nhất từ cơ sở tri thức gồm 2.050 tài liệu để tăng cường (augment) cho câu lệnh (prompt). Trên một bộ tiêu chuẩn thực tế (real-world benchmark) gồm 30 trường hợp được lấy hoàn toàn từ các gói npm sản phẩm (rw_01-rw_30) trải rộng trên 10 danh mục lỗi đồng thời, ThreadLearn kết hợp với toàn bộ đường ống BM25+AST đạt **điểm số 73.3% (22.0/30)**, so với 60.0% của mô hình cơ sở không tinh chỉnh và 65.0% đối với GPT-3.5-turbo sử dụng cùng một đường ống—mặc dù có số lượng tham số ít hơn khoảng 125 lần. Một phát hiện quan trọng là đường ống truy xuất chỉ mang lại lợi ích cho các mô hình đã có sẵn kiến thức chuyên ngành: mô hình cơ sở không thu được lợi ích nào từ việc truy xuất, trong khi mô hình được tinh chỉnh tăng thêm 10 điểm phần trăm. Tập dữ liệu tinh chỉnh và các kịch bản đánh giá được công khai cho cộng đồng.

**Từ khóa:** lỗi đồng thời, lỗi chạy đua, phân tích tĩnh, tinh chỉnh LLM, tạo văn bản tăng cường truy xuất, JavaScript

---

## 1. Giới thiệu (Introduction)
JavaScript bất đồng bộ (Node.js) được sử dụng rộng rãi để xây dựng các backend web, API và các dịch vụ thời gian thực. Tuy nhiên, mô hình thực thi hướng sự kiện (event-driven) và không chặn (non-blocking) khiến người lập trình rất dễ viết ra những đoạn mã chứa lỗi đồng thời tiềm ẩn. Một nghiên cứu thực nghiệm quy mô lớn (NodeCB) đã phân tích 57 lỗi đồng thời thực tế trong 53 dự án Node.js mã nguồn mở và phát hiện ra rằng 65% liên quan đến vi phạm tính nguyên tử (atomicity violations), 30% liên quan đến vi phạm thứ tự (order violations), và 93% gây ra các hậu quả nghiêm trọng như crash (dừng đột ngột), làm hỏng trạng thái cơ sở dữ liệu, hoặc treo tiến trình.

Dù những lỗi này rất phổ biến và gây hại, các công cụ tự động hiện tại vẫn còn nhiều thiếu sót. Các công cụ phân tích tĩnh dựa trên quy tắc (như các bộ quy tắc async của ESLint, ThreadSanitizer) có thể phát hiện các cấu trúc code đáng ngờ nhưng không thể giải thích hoặc sửa chúng, và chúng thường đưa ra những cảnh báo sai (false alarms) trên mã `async/await` hiện đại. Các phương pháp tiếp cận bằng mô hình ngôn ngữ lớn (LLM) có thể hiểu được ngữ nghĩa (semantics) của mã nhưng không thể chỉ ra chính xác dòng lỗi nếu không có sự hướng dẫn về mặt cấu trúc, và chúng đòi hỏi những mô hình rất lớn (từ 7 đến 32 tỷ tham số) để đạt độ chính xác tương đương.

Chúng tôi xác định 4 khoảng trống cụ thể trong những công nghệ tiên tiến nhất hiện nay:
* **G1:** Các công cụ dò lỗi dựa trên quy tắc tìm được lỗi nhưng không tạo ra được bản vá (fix).
* **G2:** Các phương pháp chỉ dùng LLM (LLM-only) bỏ qua các tín hiệu cấu trúc từ việc phân tích tĩnh và đòi hỏi các mô hình có kích thước 7B-32B tham số.
* **G3:** Chưa có công cụ hiện có nào sử dụng đầu ra của trình dò tĩnh như một ngữ cảnh cấu trúc (structured context) để dẫn dắt suy luận của LLM.
* **G4:** Không có công cụ toàn trình (end-to-end) nào bao phủ trọn vẹn quy trình *phát hiện -> giải thích -> khắc phục* cho JavaScript (Node.js).

Bài viết này đóng góp 4 điểm chính:
1. **`race_detector`**: một bộ phân tích tĩnh gồm 5 mẫu cho JavaScript (Node.js) kết hợp bộ tiền xử lý mã dựa trên AST.
2. **Tập dữ liệu Hindsight CoT**: 783 ví dụ đào tạo theo định dạng `(code, detector_output, reasoning_trace, fix)`, trong đó lý luận được viết sau khi đã biết bản sửa lỗi chính xác.
3. **Đường ống (Pipeline) ThreadLearn**: một hệ thống toàn trình giúp phát hiện, truy xuất ngữ cảnh, và tạo bản vá, được phục vụ thông qua một endpoint web FastAPI.
4. **Đánh giá**: so sánh với một LLM cơ sở và GPT-3.5-turbo trên một tập chuẩn gồm 30 lỗi JavaScript thực tế, xét trên tỷ lệ vượt qua (pass rate), độ chính xác theo từng danh mục, và nghiên cứu bóc tách (ablation study).

---

## 2. Bối cảnh (Background)

### 2.1. Phân loại lỗi đồng thời trong Node.js
Lỗi đồng thời trong JavaScript bất đồng bộ phát sinh từ mô hình vòng lặp sự kiện (event loop) đơn luồng, nơi nhiều tác vụ I/O có thể đan xen theo những cách không xác định (non-deterministic). Bảng 1 tóm tắt các loại lỗi được xác định trong nghiên cứu NodeCB và cách chúng biểu hiện trong Node.js.

**Bảng 1: Các loại lỗi đồng thời trong Node.js (từ NodeCB)**
| Loại lỗi (Bug Type) | Tỷ lệ | Biểu hiện trong Node.js |
|---|---|---|
| Vi phạm tính nguyên tử | 65% | Hai thao tác async đè lên nhau trên cùng một trạng thái dùng chung (VD: mất bản cập nhật DB) |
| Vi phạm thứ tự | 30% | Callback thực thi trước khi thao tác phụ thuộc hoàn tất |
| Starvation (Chết đói) | 5% | Hàng đợi I/O cạn kiệt; các tác vụ trì hoãn không bao giờ được thực thi |
| Biến vòng lặp Closure | JS | `var i` được chia sẻ qua tham chiếu (reference) cho tất cả các callback `setTimeout` |

### 2.2. BM25 Retrieval
BM25 (Best Match 25) là một hàm xếp hạng xác suất để tính điểm các tài liệu dựa trên tần suất thuật ngữ (term frequency) và nghịch đảo tần suất tài liệu (inverse document frequency) kèm theo chuẩn hóa độ dài. Chúng tôi ưu tiên BM25 thay vì tìm kiếm vector (dense vector search) bởi vì việc khớp tên API một cách chính xác (ví dụ: `setTimeout`, `appendFile`) mang lại khả năng truy xuất tốt hơn so với độ tương đồng ngữ nghĩa đối với các mẫu đồng thời JavaScript.

### 2.3. Tinh chỉnh QLoRA (QLoRA Fine-Tuning)
QLoRA cho phép tinh chỉnh các mô hình LLM đã được lượng tử hóa (quantized LLMs) bằng cách áp dụng các bộ chuyển đổi thích ứng hạng thấp (Low-Rank Adaptation adapters) lên một mô hình cơ sở lượng tử 4-bit NF4. Chỉ các trọng số của adapter mới được cập nhật trong quá trình đào tạo, giữ cho mức sử dụng bộ nhớ GPU đủ thấp để có thể chạy trên một GPU laptop duy nhất. Chúng tôi dùng rank r = 16 và hệ số chia tỷ lệ α = 32.

---

## 3. Các công trình liên quan (Related Work)

### 3.1. Phương pháp heuristic và dựa trên quy tắc
Các bộ phân tích tĩnh dựa trên quy tắc phát hiện các lỗi đồng thời bằng cách so khớp mã với các mẫu được xác định trước. ThreadSanitizer chèn mã để phát hiện race condition khi runtime nhưng chỉ hoạt động trên C/C++ và Java. ESLint cung cấp các rule bất đồng bộ cho JS, nhưng bị giới hạn ở các kiểm tra cú pháp và bỏ sót lỗi ngữ nghĩa liên quan đến trạng thái dùng chung qua nhiều callback. Hạn chế cốt lõi của công cụ rule-based là chỉ phát hiện nghi ngờ chứ không sinh được cách sửa.

### 3.2. Phương pháp tiếp cận dựa trên ML và LLM
CodeBERT và CodeT5 được dùng để tóm tắt mã và phát hiện lỗi nhưng không nhắm cụ thể vào lỗi đồng thời. PCWMs sử dụng Prompting with Chain-of-Thought World Models đạt độ chính xác 75.2% trong việc phát hiện lỗi đồng thời nhưng lại phụ thuộc vào các mô hình lớn (7B-32B). ThreadLearn khác biệt ở chỗ kết hợp cả việc phát hiện, tạo bản vá, tập trung vào JS và áp dụng tinh chỉnh quy mô nhỏ.

---

## 4. Phương pháp Đề xuất (Proposed Approach)

### 4.1. Tập dữ liệu (Dataset)
Nghiên cứu của chúng tôi sử dụng ba tập dữ liệu riêng biệt:
* **Tập dữ liệu tinh chỉnh:** 783 mẫu JSONL `(code, detector_output, reasoning_trace, fix)`, trong đó reasoning được viết muộn (hindsight). Gồm 332 dữ liệu tổng hợp (synthetic) và 451 mẫu sinh tự động.
* **Cơ sở tri thức:** 2.050 tài liệu JS (MDN, thư viện, mô tả pattern).
* **Bộ đánh giá thực tế:** 30 lỗi bất đồng bộ thực tế lấy từ các gói npm (request, mysql, async, pg...). Không có trường hợp nào là synthetic.

### 4.2. Tiền xử lý dữ liệu và Chiến lược đánh giá
**Tiền xử lý AST:** Cung cấp 4 hàm `stripComments`, `normalizeWhitespace`, `extractFunctions`, `extract_keywords` dựa trên esprima. Các từ khóa Identifier được giữ nguyên CamelCase để query BM25 tốt hơn.
**Chiến lược đánh giá:** Đánh giá PASS (tạo ra cấu trúc sửa lỗi đúng mẫu: VD Promise.all, try/catch), PARTIAL (có code nhưng chưa đúng mẫu), và FAIL (không tạo ra được đoạn code nào).

### 4.3. Kiến trúc Mô hình (Model Architecture)
Hệ thống gồm 5 module tuần tự:
1. **Dò tĩnh (Static detection):** `race_detector` quét mã bằng O(n) sinh ra `pattern_id, line_range, description`.
2. **Trích xuất từ khóa:** Lấy ra các token Identifier làm query BM25.
3. **Truy xuất tài liệu:** BM25 chấm điểm và trả về Top 3 tài liệu từ kho 2050 docs.
4. **Tạo bản vá:** LLM đã fine-tune (Qwen 1.5B) nhận tất cả (report, doc, buggy code) để xuất ra chuỗi suy nghĩ CoT và code đã fix.

#### Công cụ Dò tĩnh (Static Race Detector)
Gồm 5 pattern: `closure_loop_var`, `shared_var_settimeout`, `promise_no_await`, `concurrent_write_array`, `counter_no_atomic`.
#### Tinh chỉnh CoT nhận thức muộn (Hindsight CoT)
Tinh chỉnh Qwen2.5-Coder-1.5B với QLoRA trên 783 mẫu, neo bởi `pattern_id` và `line_range` lấy từ trình dò tĩnh.

---

## 5. Kết quả Thực nghiệm và Thảo luận (Experimental Results and Discussions)

Tất cả các thử nghiệm được chạy trên Kaggle (T4 GPU, OpenAI API). Đánh giá 6 cấu hình: (Base, Fine-tuned, GPT-3.5) x (Có Pipeline, Không Pipeline).

### 5.1 Kết quả Không dùng Pipeline
Không có BM25, tất cả mô hình đạt điểm 60-63% và không có trường hợp FAIL (0 FAIL). Lỗi phổ biến nhất là chúng cố cấu trúc lại thành `async/await` nhưng không xử lý hiểm họa bên dưới. ThreadLearn Merged (63.3%) vẫn vượt GPT-3.5 (61.7%), chứng minh lợi ích của việc fine-tune trên 783 mẫu CoT. (Điều này trả lời câu hỏi **G2**: thiếu định hướng cấu trúc, LLM lớn cũng không tự tìm đúng chỗ fix).

### 5.2 Kết quả Dùng BM25+AST Pipeline
Với Pipeline, ThreadLearn tăng vọt từ 63.3% lên **73.3%** (+10 điểm phần trăm), tạo ra 14 PASS. GPT-3.5 chỉ tăng nhẹ lên 65%. 
Đáng ngạc nhiên, mô hình base (không fine-tune) khi gắn thêm pipeline thì điểm không đổi (60%), và còn dính thêm 2 ca FAIL.

### 5.3 Bóc tách (Ablation Study)
1. **Fine-tune là điều kiện tiên quyết cho pipeline:** Mô hình base không thu được lợi gì từ pipeline, thậm chí bị nhiễu do tài liệu.
2. **Pipeline khuyếch đại Fine-tune:** Bản thân fine-tune chỉ thêm +3.3%, nhưng khi có Pipeline nó đẩy điểm lên thêm +10% (gấp 3 lần).
3. **ThreadLearn đánh bại GPT-3.5:** ThreadLearn đạt 73.3% > GPT-3.5 (65.0%) dù nhỏ hơn 125 lần, nhờ học được kiến thức chuyên ngành.

### 5.4 Phân tích theo từng Danh mục (Per-Category)
ThreadLearn mạnh nhất ở Unhandled Rejection (90%) và Sequential Awaits (100%). Race Condition đạt 70%.
Các hạng mục khó như Zalgo, Double Callback chỉ đạt 50% vì chúng cần LLM theo dõi thứ tự triệu gọi ngữ nghĩa xuyên qua các callback, một việc quá sức so với 1.5B parameter.

### 5.5 Độ trễ (Inference Latency)
Các mô hình local (Qwen, ThreadLearn) tốn khoảng 25-26 giây, chậm hơn GPT-3.5 API (~1.8 giây) khoảng 13-14 lần. Sự đánh đổi ở đây là sự riêng tư và chi phí 0 đồng vì máy tính xử lý cục bộ 100%. BM25 Pipeline chỉ tốn < 0.5s.

---

## 6. Kết luận và Hướng Nghiên cứu (Conclusion)
ThreadLearn thu hẹp khoảng cách giữa phát hiện tĩnh và sửa chữa tự động bằng cách kết hợp trình dò tĩnh 5 mẫu với mô hình ngôn ngữ 1.5B được fine-tune bằng CoT và pipeline RAG (BM25+AST). ThreadLearn đạt điểm 73.3%, bỏ xa GPT-3.5, đóng vai trò công cụ toàn trình đầu tiên nối liền `ESLint/ThreadSanitizer` và sửa chữa thực tế. Nguyên lý cốt lõi rút ra: BM25/RAG chỉ có ích khi LLM đã có tri thức ngành (domain-knowledge fine-tuning). 

Tương lai có thể mở rộng AST sang TypeScript, thêm mẫu mutex, hoặc đào tạo Qwen-7B để đưa tỷ lệ sửa lỗi Zalgo/Race Condition lên cao hơn nữa.
 
