# HANDOVER: AI2 → AI1

**Ngày:** 2026-06-11  
**Từ:** AI2 (Trung)  
**Gửi:** AI1  
**Mục tiêu:** Mở rộng test suite 20 → 100 cases + bổ sung tài liệu knowledge base

---

## 1. Tổng quan những gì AI2 vừa hoàn thành

### 1.1 Eval pipeline mới (ai2/)

AI2 đã xây dựng hệ thống đánh giá hoàn chỉnh với 5 script:

| File | Mô tả | Output |
|------|-------|--------|
| `ai2/eval_baseline.py` | Qwen2.5-Coder-1.5B gốc qua HF API | `eval_base_results.json` |
| `ai2/eval_local_base.py` | Qwen base inference local (model gốc) | `eval_base_results.json` |
| `ai2/eval_local_merged.py` | ThreadLearn fine-tuned local, NO RAG | `eval_merged_results.json` |
| `ai2/eval_rag_merged.py` | ThreadLearn fine-tuned local, **WITH RAG** | `eval_rag_results.json` |
| `ai2/eval_openai.py` | GPT-3.5-turbo zero-shot (baseline so sánh) | `eval_openai_results.json` |
| `ai2/rescore_merged.py` | Rescore lại kết quả bằng pattern matching | `eval_merged_rescored.json` |

### 1.2 Kết quả eval hiện tại (20 test cases)

| Model | Pass | Pass Rate |
|-------|------|-----------|
| ThreadLearn + RAG (Ours) | 15/20 | **75%** |
| ThreadLearn RAW (no RAG) | 14/20 | **70%** |
| Qwen2.5-Coder base | 8/20 | 40% |
| GPT-3.5-turbo zero-shot | 6/20 | 30% |

Chi tiết xem: `ai2/EVAL_REPORT.md`

### 1.3 Cải tiến AST-based BM25 (AI2-06)

RAG pipeline (`ai2/server/rag_pipeline.py`) đã được nâng cấp:
- **Cũ:** tokenize bằng regex → split `setTimeout` thành `["set","timeout"]`
- **Mới:** dùng `ast_preprocessor.extract_keywords()` (esprima) → giữ nguyên `setTimeout`, `appendFile`, `Promise`
- Kết quả: BM25 retrieval chính xác hơn, +5pp pass rate so với RAW

### 1.4 Format prompt đúng (quan trọng!)

```
Convert to concurrent JavaScript:\n\n{code}\n
```

**KHÔNG dùng chat template.** Dùng sai format này sẽ mất ~35pp pass rate. Tất cả eval script đã dùng đúng format này.

---

## 2. Yêu cầu từ AI2 gửi AI1

### 2.1 Mở rộng test suite: 20 → 100 cases

**File cần sửa:** `ai2/eval_rag_merged.py` (và các eval script khác)

Test cases hiện tại nằm trong biến `TEST_CASES` bên trong mỗi script (hardcoded). AI1 cần:

#### Bước 1 — Tạo file test case riêng biệt

Tạo file: `ai2/test_cases/test_suite_v2.json`

Format mỗi test case:
```json
{
  "id": "test_021",
  "category": "Race Condition",
  "difficulty": "medium",
  "description": "Mô tả ngắn vấn đề",
  "code": "// JS code có bug concurrent",
  "expected_fix_pattern": ["Promise.all", "async/await"],
  "tags": ["setTimeout", "shared-state"]
}
```

#### Bước 2 — Phân bổ 100 cases theo category

Hiện tại 20 cases có phân bổ lệch (Race Condition 5, Event Loop 5, còn lại 1 mỗi loại). 100 cases cần cân bằng hơn:

| Category | Cases hiện tại | Cần thêm | Tổng |
|----------|---------------|----------|------|
| Race Condition | 5 | +10 | 15 |
| Event Loop Blocking | 5 | +10 | 15 |
| Unhandled Rejection | 1 | +9 | 10 |
| Promise Anti-patterns | 1 | +9 | 10 |
| Callback Hell | 1 | +9 | 10 |
| Context Loss (this) | 1 | +7 | 8 |
| Zalgo (sync/async mix) | 1 | +7 | 8 |
| Resource Exhaustion | 1 | +7 | 8 |
| Sequential Awaits | 1 | +7 | 8 |
| Missing Promise.all | 1 | +7 | 8 |
| **Total** | **18** | **82** | **100** |

> Double Callback và Buffer Leak ghép vào category gần nhất.

#### Bước 3 — Cập nhật eval scripts để load từ file

Sửa `ai2/eval_rag_merged.py` dòng load TEST_CASES:
```python
# Cũ: hardcoded list
TEST_CASES = [{"id": "test_01", ...}, ...]

# Mới: load từ file
import json
with open(os.path.join(os.path.dirname(__file__), "test_cases", "test_suite_v2.json")) as f:
    TEST_CASES = json.load(f)
```

Áp dụng tương tự cho: `eval_local_base.py`, `eval_local_merged.py`, `eval_baseline.py`, `eval_openai.py`

### 2.2 Bổ sung tài liệu knowledge base

**File:** `ai2/knowledge-base/knowledge_base.json`  
Hiện có **2050 docs**. BM25 RAG dùng file này để retrieve context.

AI1 cần bổ sung docs cho các category còn yếu (pass rate thấp). Xem `ai2/EVAL_REPORT.md` Section 3 để biết test nào đang FAIL/PARTIAL.

Format mỗi doc trong knowledge_base.json:
```json
{
  "id": "doc_2051",
  "title": "Fixing Race Condition with Mutex Pattern in Node.js",
  "category": "Race Condition",
  "content": "Nội dung giải thích kỹ thuật...\n\nExample:\n```javascript\n// code example\n```",
  "tags": ["mutex", "async-lock", "shared-state"],
  "source": "manual"
}
```

Ưu tiên bổ sung docs cho các pattern AI2 đang PARTIAL:
- `test_04`: Singleton promise initialization race
- `test_05`: `appendFile` concurrent write (RAG context đang làm confused)
- `test_17`: EventEmitter memory leak pattern
- `test_18`: Closure capture trong loop

Script augment: `ai2/knowledge-base/augment_dataset.py` — AI1 có thể dùng script này để tự động sinh thêm docs.

### 2.3 Cập nhật scoring logic

**File:** `ai2/rescore_merged.py`

Hiện tại `PASS_PATTERNS` chỉ match string đơn giản. Khi có 100 cases với nhiều pattern hơn, cần mở rộng:

```python
# Thêm patterns cho categories mới
PASS_PATTERNS = {
    "Race Condition": [
        r"await.*Promise\.all",
        r"async.*lock|mutex",
        r"\.acquire\(\)|\.release\(\)",   # thêm mới
    ],
    "Event Loop Blocking": [
        r"setImmediate|process\.nextTick",
        r"worker_threads|Worker",
        r"fs\.promises\.",
        r"\.pipe\(|stream\.",              # thêm mới
    ],
    # ... thêm categories mới
}
```

---

## 3. Cấu trúc file AI2 cần AI1 hiểu

```
ThreadLearn-AI-Trainning/
├── ai2/
│   ├── eval_baseline.py          # HF API eval (Qwen base)
│   ├── eval_local_base.py        # Local eval (Qwen base, no fine-tune)
│   ├── eval_local_merged.py      # Local eval (ThreadLearn, no RAG)
│   ├── eval_rag_merged.py        # Local eval (ThreadLearn + RAG) ← MAIN EVAL
│   ├── eval_openai.py            # GPT-3.5 baseline
│   ├── rescore_merged.py         # Rescore từ JSON output
│   ├── EVAL_REPORT.md            # Báo cáo đầy đủ kết quả
│   ├── eval_rag_results.json     # Kết quả RAW vs RAG (20 cases)
│   ├── eval_merged_results.json  # Kết quả ThreadLearn no RAG
│   ├── eval_base_results.json    # Kết quả Qwen base
│   ├── eval_openai_results.json  # Kết quả GPT-3.5
│   ├── eval_merged_rescored.json # Rescored results
│   ├── knowledge-base/
│   │   ├── knowledge_base.json   # 2050 docs BM25 index
│   │   └── augment_dataset.py    # Script sinh thêm docs
│   └── server/
│       ├── rag_pipeline.py       # RAG pipeline (AST keyword extraction)
│       ├── bm25_module.py        # BM25 retriever
│       ├── llm_client.py         # LLM interface
│       └── ...
├── ai1/
│   └── modules/
│       └── ast_preprocessor.py   # ← AI2 dùng hàm extract_keywords() ở đây
└── models/
    ├── base/                     # Qwen2.5-Coder-1.5B gốc (tokenizer)
    └── merged/                   # ThreadLearn fine-tuned (LoRA merged)
```

---

## 4. Môi trường chạy eval

```bash
# Dependencies
pip install esprima transformers torch bm25 fastapi

# Chạy eval chính (cần GPU hoặc CPU đủ RAM ~4GB)
cd ai2
python eval_rag_merged.py

# Output sẽ ghi vào eval_rag_results.json
```

**Model path:** `../models/merged/` (ThreadLearn fine-tuned)  
**Device:** tự động detect GPU (CUDA) hoặc fallback CPU  
**Prompt format bắt buộc:** `"Convert to concurrent JavaScript:\n\n{code}\n"`

---

## 5. Checklist AI1 cần hoàn thành

- [ ] Tạo `ai2/test_cases/test_suite_v2.json` với 100 test cases
- [ ] Phân bổ đều theo 10 category, đúng format JSON ở Mục 2.1
- [ ] Cập nhật `eval_rag_merged.py` load test từ file (không hardcode)
- [ ] Cập nhật các eval script còn lại tương tự
- [ ] Bổ sung ≥50 docs vào `knowledge_base.json` cho categories yếu
- [ ] Mở rộng `PASS_PATTERNS` trong `rescore_merged.py` cho patterns mới
- [ ] Chạy thử `eval_rag_merged.py` với 100 cases, verify không crash
- [ ] Cập nhật `ai2/EVAL_REPORT.md` với kết quả 100-case mới

---

## 6. Lưu ý quan trọng

1. **Không thay đổi prompt format** — `"Convert to concurrent JavaScript:\n\n{code}\n"` là training format. Sai format = kết quả sai hoàn toàn.

2. **Token HF** — `HF_TOKEN` phải lấy từ env var `os.environ.get("HF_TOKEN", "")`. **Không hardcode token vào code** — GitHub sẽ block push (đã xảy ra, mất thời gian fix).

3. **esprima dependency** — `ast_preprocessor.py` dùng `esprima`. Nếu chưa cài: `pip install esprima`. Có fallback regex nếu không có.

4. **Model path** — `eval_local_*.py` dùng path `../models/merged/`. Nếu chạy trên máy khác, cần tải model từ HuggingFace: `anha12/threadlearn-qwen2.5-coder-1.5b-merged`.

5. **Test case ID** — Giữ format `test_NNN` (3 chữ số), bắt đầu từ `test_021` cho cases mới.
