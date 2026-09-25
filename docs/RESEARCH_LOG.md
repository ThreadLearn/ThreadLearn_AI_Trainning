# ThreadLearn — Research Log

Theo dõi tiến trình nghiên cứu: model nào đã train, eval ra sao, quyết định nào đã chốt — và tại sao. Cập nhật khi có milestone mới (model mới, kết quả eval mới, thay đổi pipeline).

---

## Timeline

### Giai đoạn 1 — Dataset & Detector (hoàn tất)

- **AI1**: Thu thập 783 cặp code lỗi/đã sửa (`training/data/raw/bugsjs_*.jsonl`, sinh bởi `generate_bugsjs.py` + `generate_bugsjs_batch3.py`). Format JSONL completion-style cho SFTTrainer (`ai1_02_format_jsonl.py`).
- **AI2**: Knowledge base 2050 tài liệu JS concurrency (`server/knowledge-base/knowledge_base.json`). BM25 retrieval (`bm25_module.py`) + AST keyword extraction (`ast_preprocessor.py`). Static race detector 10 pattern (`race_detector.py`).
- **AI2**: FastAPI server hoàn chỉnh — `/health`, `/analyze`, `/history`, JWT auth, Redis cache, MongoDB history.

### Giai đoạn 2 — Model v1 (ThreadLearn Merged, hoàn tất)

- Fine-tune `Qwen2.5-Coder-1.5B` bằng QLoRA (r=16, α=32, 4-bit NF4) trên 783 mẫu, format `"Convert to concurrent JavaScript:\n\n{code}\n"` → completion.
- Merge LoRA adapter vào base model → `anha12/threadlearn-qwen2.5-coder-1.5b-merged` (HuggingFace Hub), lưu local tại `models/merged/`.
- **Eval 20-case** (`training/evaluation/`, `server/eval/`): RAW 70%, +RAG 75%.
- **Eval 30-case real-world** (`server/tests/real_world/`, bug thật từ npm packages production):

  | Model | Pass | Score | % |
  |---|---|---|---|
  | Base (no fine-tune) | 6/30 | 18.0 | 60.0% |
  | Merged v1 (no pipeline) | 8/30 | 19.0 | 63.3% |
  | GPT-3.5-turbo (no pipeline) | 7/30 | 18.5 | 61.7% |
  | Base + pipeline | 8/30 | 18.0 | 60.0% |
  | **Merged v1 + pipeline** | **14/30** | **22.0** | **73.3%** |
  | GPT-3.5-turbo + pipeline | 9/30 | 19.5 | 65.0% |

  → Pipeline (BM25+AST) chỉ giúp model đã fine-tune (+3.0 pts / +10pp); không giúp base (+0 pts); giúp GPT-3.5 ít (+1.0 pt). Kết luận: pipeline khuếch đại domain knowledge sẵn có, không tạo ra domain knowledge.

### Giai đoạn 3 — Model v2 / CoT (đang đánh giá — đây là điểm hiện tại)

Ân huấn luyện thêm một bản model mới: `anha12/threadlearn-qwen2.5-coder-1.5b-cot-v2` — chưa có trong repo (chỉ tồn tại trên Kaggle/HF của Ân), thêm reasoning/Chain-of-Thought vào quá trình train so với v1.

**Eval 30-case real-world** (`server/tests/real_world/results/`):

| Model | Pass | Partial | Fail | Score | % |
|---|---|---|---|---|---|
| Merged v1 (no pipeline) | 8 | 22 | 0 | 19.0/30 | 63.3% |
| Merged v1 + pipeline | 14 | 16 | 0 | 22.0/30 | 73.3% |
| **Merged v2 (no pipeline)** | **16** | **14** | **0** | **23.0/30** | **76.7%** |
| **Merged v2 + pipeline** | **9** | **20** | **1** | **19.0/30** | **63.3%** |

**Phát hiện chính — đây là vấn đề user đặt ra:**

v2 đứng một mình (không pipeline) là model tốt nhất từ trước đến giờ: 76.7%, vượt cả v1+pipeline (73.3%). Nhưng khi gắn pipeline vào, v2 **tụt xuống 63.3%** — bằng đúng v1 *không* pipeline, tức là pipeline xóa sạch toàn bộ lợi ích fine-tuning CoT mang lại.

So sánh per-case: 10/16 case mà v2 PASS khi không pipeline bị tụt xuống PARTIAL/FAIL khi thêm pipeline (`rw_03, 04, 06, 07, 11, 12, 14, 15, 17, 18`).

**Root cause (đã xác định, đọc trực tiếp response output)** — ví dụ `rw_04`:

```
=== KHÔNG pipeline (PASS) ===
app.use(async function(req, res, next) {
  const transformed = await Promise.all(...)
  ...

=== CÓ pipeline (PARTIAL) ===
Reference 3 — Data Dependency: Hitting the Database Multiple Times [data-dependency]:
Fetching data from the database multiple times...
```

Model v2+pipeline không sinh code fix — nó **echo lại nguyên văn đoạn context retrieved** thay vì áp dụng vào bug thực tế. Đây là dấu hiệu kinh điển của **prompt format mismatch** (xem `README.md` mục 8, Lỗi #4 — y hệt vấn đề từng gặp ở v1 lúc lệch eval/train format, làm rớt từ 70% xuống 35%).

**Đối chiếu 3 prompt template khác nhau đang tồn tại trong codebase:**

| Nguồn | Format context |
|---|---|
| Training v1 (`ai1_02_format_jsonl.py`) | Không có context, chỉ `"Convert to concurrent JavaScript:\n\n{code}\n"` |
| `server/server/rag_pipeline.py` (production, `_build_prompt`) | `<reference_docs>` tag, label **"Tài liệu {i}"** (tiếng Việt), context **SAU** code |
| Notebook eval v2+pipeline (`kaggle_pipeline_merged_v2.ipynb`, `build_prompt`) | Không tag, label **"Reference {i}"** (tiếng Anh), context **TRƯỚC** code, content cắt 500 ký tự |

Notebook eval v2 không-pipeline dùng đúng format training gốc (`"Convert to concurrent JavaScript:\n\n{code}\n"`, không context) và đạt 76.7% — xác nhận **training format của v2 không đổi so với v1**. Vấn đề chỉ nằm ở cách notebook with-pipeline tự chế ra format "Reference {i}" mới, **khác cả 2** format đã biết (khác training, khác `rag_pipeline.py` production) — chưa từng được test đúng cách.

→ Đây không phải giới hạn của model v2. Đây là bug thử nghiệm: pipeline injection chưa từng dùng đúng format mà model quen nhận.

---

## Trạng thái hiện tại

- Model v1 (`merged`) đang chạy production trong `server/server/` qua `models/merged/`.
- Model v2 (CoT) **chưa migrate vào repo** — chỉ có kết quả eval từ notebook Kaggle, chưa có file model local, chưa tích hợp `rag_pipeline.py`.
- Pipeline production (`_build_prompt` trong `rag_pipeline.py`) chưa từng được test trực tiếp với v2 — số liệu "63.3%" ở trên đến từ format khác (notebook), không phải từ code production thật.

→ **Chưa thể kết luận "pipeline không hợp với v2"**. Mới chỉ biết "1 cách nhét context cụ thể (chưa khớp format nào) làm hại v2". Cần test lại bằng đúng format `rag_pipeline.py` trước khi kết luận.

Kế hoạch chi tiết: xem [`MIGRATION_PLAN_v2.md`](MIGRATION_PLAN_v2.md).

---

## Giai đoạn 4 — Mở rộng Knowledge Base cho pipeline (2055 → ~2150+ doc)

**Vấn đề:** KB retrieval (BM25) cho pipeline chỉ có 2055 doc, phân bố lệch nặng —
69% rơi vào category "patterns" chung chung, không map theo 18 `pattern_id` mà
`race_detector.py` thực sự dùng. Một số pattern gần như trắng: `concurrent_write_array`,
`context_loss_this`, `resource_exhaustion`, `missing_join` đều 0 doc; `zalgo`,
`double_callback`, `promise_no_await`, `buffer_leak` dưới 10 doc.

**Đã làm:**
1. `tag_pattern_ids.py` — gán field `pattern_ids` cho 2055 doc cũ theo keyword rule bám
   sát `race_detector.py` (814 doc match được, còn lại giữ nguyên category cũ, không đoán bừa).
2. `add_gap_docs.py` (+8 doc) + `add_gap_docs_round2.py` (+4 doc) — bù 4 pattern trắng
   bằng nguồn thật (GitHub Issues/PR), 4 pattern mỏng bằng viết tay dựa MDN/Node.js docs.
3. `add_batch1_docs.py` (+45) + `add_batch2_docs.py` (+45) — viết tay mở rộng 6 pattern
   mỏng nhất (zalgo, double_callback, promise_no_await, buffer_leak, concurrent_write_array,
   context_loss_this), mỗi pattern 15 doc mới, mỗi doc là 1 tình huống code cụ thể khác
   nhau (framework/API/context khác nhau: Express, cron, WebSocket, Electron IPC, GraphQL
   resolver, Sequelize, Chart.js...) — không phải paraphrase 1 câu gốc.

**Tradeoff quy mô vs chất lượng (quan trọng, tránh bị hỏi ngược khi phản biện):**

User ban đầu đặt mục tiêu KB đạt 5000 doc (ngưỡng `auto_stopwords.py` tự chuyển
sang IDF auto-stopwords). Tính toán thực tế: để mỗi doc mới thực sự riêng biệt
(không phải đổi từ đồng nghĩa của cùng 1 câu — BM25 sẽ retrieve các doc gần giống
nhau, không tăng thông tin thật), cần thiết kế ~270 tình huống code khác nhau MỖI
pattern (bám 18 pattern) — vượt xa khả năng viết tay có kiểm soát trong 1 phiên làm
việc. Đã thống nhất với user: **ưu tiên tính riêng biệt, hạ mục tiêu xuống ~400-500
doc mới** (không chạm 5000), viết theo batch (mỗi batch 1 người tự viết nội dung
thật cho 1 nhóm pattern, không dùng template rỗng ghép câu công thức).

**Cập nhật (sau batch 9):** đã làm hết 18/18 pattern_id — mỗi pattern giờ có tối
thiểu ~30 doc riêng biệt (trước đó nhiều pattern ở mức 0-9). KB hiện **2432 doc**
(2055 → 2432, +377, qua 11 lượt: tag + gap + round2 + 9 batch). Phân bố còn lệch
tự nhiên do 2 pattern gốc vốn đã dày sẵn (`shared_var_settimeout` 553,
`shared_list_no_lock` 106) không cần thêm.

**Kết luận cho báo cáo:** KB hiện 2432 doc, KHÔNG đạt ngưỡng 5000. Nếu ban giám
khảo hỏi về quy mô KB, trả lời trung thực: ưu tiên chất lượng/tính đa dạng ngữ
cảnh hơn số lượng thô — mỗi doc mới là 1 tình huống lỗi thực tế riêng biệt
(framework/API/context khác nhau: Express, cron, WebSocket, Kafka, Lambda,
worker_threads...), không phải nhân bản để đạt KPI số lượng. Muốn đạt 5000 đúng
nghĩa cần thêm thời gian đáng kể (nhiều batch nữa) hoặc quy trình crawl/sinh có
review tự động ở quy mô lớn hơn — chưa làm trong lần này.
