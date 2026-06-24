# CLAUDE.md

Hướng dẫn cho Claude Code khi làm việc trong repo này. Đọc trước khi sửa code.

## Dự án

**ThreadLearn** — phát hiện & sửa lỗi concurrency JavaScript bằng fine-tuned LLM + RAG.
Môn WDP301, FPT University. Tác giả: Lê Trí Trung (AI2), Hà Văn Ân (AI1).

Hai module độc lập:
- **AI1** (`ai1/`) — thu thập dataset + QLoRA fine-tune `Qwen/Qwen2.5-Coder-1.5B`. Python.
- **AI2** (`ai2/`) — RAG pipeline (BM25) + FastAPI server `/analyze`. Python 3.13+.
- Phụ trợ: `mock-website/` (demo UI: frontend HTML/React + Express proxy), `models/` (base + merged), `docs/` (research, trackers).

Luồng runtime: `code JS → AST keyword extract → BM25 top-3 docs → prompt → LLM → fix code`.

## Lệnh thường dùng

```bash
# --- AI2 server ---
cd ai2/server
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8001   # Windows
uvicorn main:app --reload --port 8001              # Linux/Mac
curl http://localhost:8001/health                  # → {"status":"ok","retriever_docs":2055}

# Smoke test (cách agent verify server — tự start, gọi 3 HTTP call, assert, stop)
cd ai2/server && bash ../.claude/skills/run-ai2-server/smoke.sh

# --- Tests ---
cd ai2/server && pytest ../tests/ -v               # unit tests
cd ThreadLearn_AI_Trainning && pytest ai2/tests/ -v

# --- Evaluation (inference thật, cần model merged tải về models/merged/) ---
cd ai2 && python eval/scripts/eval_rag_merged.py   # → eval/results/eval_merged_*.json

# --- AI1 pipeline ---
cd ai1/modules && python ai1_01_dataset_collector.py   # cần GITHUB_TOKEN
python ai1_02_format_jsonl.py                          # → JSONL cho SFTTrainer
# ai1_03_finetune.py chạy trên Kaggle (2×T4); rồi:
cd ai1/training && python ai1_04_merge_model.py
```

## Quy ước & ràng buộc quan trọng

1. **Prompt format = "completion", KHÔNG phải chat/ChatML.** Model train với
   `f"Convert to concurrent JavaScript:\n\n{code}\n"` (xem `ai1/modules/ai1_02_format_jsonl.py`).
   Mọi inference/eval/prompt RAG PHẢI dùng đúng format này. Dùng `apply_chat_template` làm pass rate tụt 70% → 35%. Đây là lỗi tốn nhiều thời gian nhất của dự án (README Lỗi #4).

2. **Số liệu eval chính thức: RAW 14/20 (70%), +RAG 15/20 (75%)** — từ inference thật.
   Con số **18/20 (90%)** trong `ai1/README.md` là SAI (suy ra từ mock LLM), đã bị bác bỏ (README Lỗi #5). Không trích dẫn 90%.

3. **Knowledge base active = `ai2/knowledge-base/knowledge_base.json` (2055 docs).** Đây là file `config.py` trỏ tới. STRUCTURE.md và `smoke.sh` còn ghi "250" là số cũ — đừng tin. `knowledge_base_extended.json` (2107 docs) không phải file đang dùng.
   Thêm doc: **append** id kế tiếp (`js-...`), không sửa/xoá doc cũ. Index BM25 rebuild mỗi lần server start (<500ms).

4. **`config.py` load `.env` lúc import.** Env var set ở shell SAU khi Python chạy sẽ bị bỏ qua — luôn sửa file `ai2/server/.env`. `JWT_SECRET` phải khớp Node.js backend. **Không commit `.env`.**

5. **`LLM_PROVIDER`**: `mock` (default cho dev/test — trả Issue cứng, không phải inference thật) | `openai` | `ollama` | `hf_inference`. Lưu ý: default trong `config.py` hiện là `ollama`.

6. **Merge LoRA phải dùng CPU + fp16**, không quantize/GPU (`ai1_04_merge_model.py`). Load 4-bit sẽ lỗi `cannot merge ... load_in_4bit`.

7. **Windows gotchas**: tránh ký tự Unicode (`→`) trong `print()` (cp1252 crash — dùng ASCII `->`); port 8001 bận → `netstat -ano | findstr :8001` rồi `taskkill /PID <pid> /F`; tên file tải từ HF có thể thành `model (1).safetensors` → rename.

8. **Concurrency control**: `_llm_semaphore = asyncio.Semaphore(3)` giới hạn 3 LLM call song song; vượt → queue, đầy slot → 429. Cần Python 3.11+ (dùng `asyncio.timeout`).

## Import chain AI2

`main.py` → `rag_pipeline.py` → `bm25_module.py` + `llm_client.py` + `race_detector.py` → `report_formatter.py`.
AI2 import trực tiếp module của AI1 từ `ai1/modules/` (`ast_preprocessor`, `output_parser`).

## Skills có sẵn

- `run-ai2-server` (scope `ai2/`) — start/smoke-test/verify FastAPI server. Ưu tiên dùng skill này khi cần chạy hoặc kiểm tra server thay vì tự dựng lệnh.

## Cách làm việc (yêu cầu của chủ dự án)

- **Phân nhỏ công việc** thành các bước rõ ràng; dùng TodoWrite cho task nhiều bước.
- **Ưu tiên dùng skill** phù hợp (vd `run-ai2-server`, `code-review`, `verify`) để có kết quả tốt nhất.
- **Lưu ý phạm vi code (scope)**: chỉ sửa đúng phần liên quan tới yêu cầu, không lan sang AI1/AI2/docs khác nếu không cần.
- **KHÔNG sửa nội dung đã chốt** trong các file/message trước (README.md, docs/*, content đã finalize). Chỉ thêm mới hoặc sửa khi được yêu cầu rõ ràng.
- Nếu yêu cầu mơ hồ hoặc có mâu thuẫn dữ liệu → hỏi lại trước khi làm.
