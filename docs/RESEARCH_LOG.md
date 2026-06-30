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
