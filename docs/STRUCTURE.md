# ThreadLearn AI — Project Structure

```
ThreadLearn-AI-Trainning/
├── training/                          # AI1 — Ân: Fine-tune & AST
│   ├── data/
│   │   ├── raw/                  # bugsjs_*.jsonl, generate_bugsjs*.py, dataset_review_report.txt
│   │   └── processed/            # ast_dataset.json
│   ├── training/                 # ai1_03_finetune.py, ai1_04_merge_model.py (QLoRA, Kaggle/RunPod)
│   ├── evaluation/                # evaluate_model.py, generate_test_cases.py, run_inference_local.py
│   ├── model/                    # exported SafeTensors (gitignored, >100MB)
│   ├── modules/                  # shared Python modules — AI2 import trực tiếp
│   │   ├── ast_preprocessor.py   # AI2 dùng cho race_detector và rag_pipeline
│   │   ├── output_parser.py      # AI2 dùng khi swap sang Ollama
│   │   ├── ai1_01_dataset_collector.py
│   │   ├── ai1_02_format_jsonl.py
│   │   ├── ai1_02b_ast_preprocessor_unused.js  # bản JS song song, không dùng trong pipeline Python
│   │   ├── DEPRECATED_patch_collector_onetime.py  # script vá lỗi ai1_01 một lần, đã chạy xong
│   │   └── dataset_validator.py    # 9 check chất lượng dataset (AI1-01)
│   ├── tests/
│   │   └── test_ast.py           # unit tests cho ast_preprocessor
│   ├── LESSONS_LEARNED.md
│   └── README.md
│
├── server/                          # AI2 — Trung: Serving, RAG & Race Condition
│   ├── knowledge-base/
│   │   ├── knowledge_base.json   # 2,050 docs concurrent JS patterns (1,418 patterns, 352 race-conditions, 280 anti-patterns)
│   │   ├── knowledge_base_extended.json
│   │   └── KNOWLEDGE_BASE_OVERVIEW.md
│   ├── server/
│   │   ├── main.py               # FastAPI app, routes, JWT middleware
│   │   ├── bm25_module.py        # BM25 indexer + search (in-memory)
│   │   ├── race_detector.py      # rule-based detector, 14 JS + 4 Python patterns (paper highlights 5 core JS patterns)
│   │   ├── report_formatter.py   # format RC output → JSON {severity, fix}
│   │   ├── rag_pipeline.py       # RAG flow code→AST→BM25→LLM→response
│   │   ├── cache.py              # Redis cache SHA256 key, TTL 24h
│   │   ├── db.py                 # MongoDB motor, ai_analysis_history
│   │   ├── llm_client.py         # LLMClient ABC → OpenAIClient/OllamaClient
│   │   ├── auth.py               # JWT auth
│   │   ├── auto_stopwords.py     # stopwords filtering cho BM25 query
│   │   ├── schemas.py            # Pydantic models
│   │   ├── output_parser.py      # parse LLM raw output
│   │   ├── config.py             # env vars: API keys, URLs, LLM provider
│   │   ├── logs/                 # server_out.log, server_err.log (gitignored)
│   │   └── requirements.txt
│   ├── eval/                     # model evaluation (base vs merged vs RAG vs OpenAI)
│   │   ├── scripts/               # eval_baseline.py, eval_local_base.py, eval_local_merged.py, eval_openai.py, eval_rag_merged.py, rescore_merged.py
│   │   └── results/               # eval_*_results.json
│   ├── tests/
│   │   ├── unit/                 # test_bm25.py, test_race_detector.py, test_rag_pipeline.py, test_cache.py, test_db.py, test_main.py, test_report_formatter.py, test_output_parser.py, conftest.py
│   │   ├── load/                 # locustfile.py
│   │   └── real_world/           # 30-case real-world benchmark
│   │       ├── cases/
│   │       ├── notebooks/        # with_pipeline/, without_pipeline/
│   │       ├── results/
│   │       └── README.md
│   ├── EVAL_REPORT.md
│   └── README.md
│
├── shared/
│   └── README.md                 # cross-team import docs, delivery schedule
│
├── docs/
│   ├── STRUCTURE.md              # this file
│   ├── AI1_PROGRESS_TRACKER.md   # Ân's task tracker
│   ├── AI2_PROGRESS_TRACKER.md   # Trung's task tracker
│   ├── AI2_TRUNG_ROADMAP.md
│   ├── reference-papers/         # PDF papers tham khảo + giải thích (NodeCB, PCWMs, ICCIES)
│   │   ├── explain_nodecb.md
│   │   ├── explain_pcwms.md
│   │   ├── *.pdf
│   │   └── *_visual.html
│   └── my-research/              # bài báo ICTA2026 — bản thảo, template, hình vẽ
│       ├── ICTA_COMPLIANCE_PLAN.md
│       ├── MIGRATION_PLAN_8pages.md
│       ├── ThreadLearn_ICTA_WordReady.md
│       ├── ThreadLearn_PASTE_BLOCKS.txt
│       ├── Trung_ThreadLearn_v2.docx   # bản docx hiện hành
│       ├── icta_word_template/         # template Springer LNCS Word (.docm)
│       ├── figures/                    # figure_1..3, figure_base
│       ├── paper_latex_source/         # bản LaTeX chính thức (llncs.cls)
│       ├── outline/                    # paper_outline_en.md, paper_outline_vi.md
│       └── paper_vietnamese/           # bản báo cáo tiếng Việt (LaTeX)
│
├── models/                       # LLM weights (config/tokenizer only, weights gitignored)
│   ├── base/                     # Qwen2.5-Coder-1.5B gốc
│   └── merged/                   # bản fine-tuned đã merge
│
├── mock-website/                 # demo UI — không thuộc core AI pipeline
│   ├── backend/                  # Node.js
│   └── frontend-react/           # React
│
├── .claude/skills/
├── .gitignore
├── .env
├── docker-compose.yml
└── README.md
```

---

## Folder Descriptions

### `training/data/raw/`
Raw dataset: cặp code đơn luồng → đa luồng, sinh từ BugsJS + viết tay.
Output: `bugsjs_train.jsonl`, `bugsjs_train_batch3.jsonl`, eval splits.

### `training/data/processed/`
Dataset sau khi format sang AST-augmented JSON: `ast_dataset.json`.

### `training/training/`
Scripts QLoRA fine-tune Qwen2.5-Coder-1.5B trên Kaggle/RunPod (`ai1_03_finetune.py`) và merge adapter vào base model (`ai1_04_merge_model.py`).

### `training/evaluation/`
Đánh giá model fine-tune: sinh test case, chạy inference local, so kết quả.

### `training/model/`
Exported model sau fine-tune. SafeTensors (~3-4GB) **gitignored** — chia sẻ qua HuggingFace Hub / Google Drive link.

### `training/modules/`
Shared Python modules do AI1 viết, AI2 import trực tiếp.
- `ast_preprocessor.py` — AI2 dùng cho race_detector và rag_pipeline
- `output_parser.py` — AI2 dùng khi swap sang Ollama
- `ai1_01_dataset_collector.py`, `ai1_02_format_jsonl.py` — script thu thập/format dataset một lần, không phải module runtime
- `ai1_02_ast_preprocessor.js` — bản port JavaScript song song, hiện không gọi từ pipeline Python

### `server/knowledge-base/`
Nguồn dữ liệu RAG: tài liệu JavaScript concurrent patterns.
BM25 index được build từ file này mỗi lần server start.
**Không sửa trực tiếp** — thêm doc mới bằng cách append vào `knowledge_base.json` với id tiếp theo.

### `server/server/`
FastAPI microservice — core của AI2.
Import chain: `main.py` → `rag_pipeline.py` → `bm25_module.py` + `llm_client.py` + `race_detector.py` → `report_formatter.py`.
Log file chạy server nằm ở `server/server/logs/` (gitignored).

### `server/eval/`
Đánh giá model end-to-end trên benchmark thực tế: so sánh base / fine-tuned / fine-tuned+RAG / GPT-3.5-turbo.
Kết quả lưu ở `server/eval/results/*.json`, dùng cho bảng ablation trong bài báo (`docs/my-research`).

### `server/tests/`
Pytest test suite. Chạy từ root:
```bash
cd ThreadLearn-AI-Trainning
pytest server/tests/unit/ -v
```
`server/tests/real_world/` chứa 30-case benchmark thực tế dùng cho Section 5 của bài báo.

### `shared/`
Không chứa code — chỉ chứa docs về cross-team dependencies và import pattern.
Khi AI1 deliver module, AI2 import thẳng từ `training/modules/`.

### `docs/`
Tài liệu kỹ thuật dùng chung cả team.
- `docs/reference-papers/` — paper tham khảo (PDF) + giải thích tiếng Việt, KHÔNG phải bài viết của nhóm.
- `docs/my-research/` — bài báo ICTA2026 của nhóm, bản thảo + template + hình vẽ.

### `models/`
Config/tokenizer của base model và merged model. Trọng số thực (`.safetensors`) gitignored — tải qua HuggingFace Hub.

### `mock-website/`
Demo web UI (React + Node.js backend) minh hoạ tích hợp AI2 vào sản phẩm thật. Không bắt buộc để chạy core pipeline.

---

## Key Files Quick Reference

| File | Vai trò | Trạng thái |
|------|---------|------------|
| `server/knowledge-base/knowledge_base.json` | RAG corpus | ✅ DONE |
| `server/server/bm25_module.py` | BM25 retrieval | ✅ DONE |
| `server/server/race_detector.py` | Static race detector | ✅ DONE |
| `server/server/report_formatter.py` | Format kết quả | ✅ DONE |
| `server/server/main.py` | FastAPI app | ✅ DONE |
| `server/server/rag_pipeline.py` | RAG end-to-end | ✅ DONE |
| `server/server/cache.py` | Redis cache | ✅ DONE |
| `server/server/llm_client.py` | LLM abstraction | 🚫 Ollama swap blocked (AI1-07) |
| `server/server/db.py` | MongoDB history | ✅ DONE |
| `training/modules/ast_preprocessor.py` | AST preprocessing | ✅ DONE |
| `training/modules/output_parser.py` | Parse LLM output | ✅ DONE |
| `training/training/ai1_03_finetune.py` | QLoRA fine-tune | ✅ DONE |
| `server/eval/scripts/eval_rag_merged.py` | Ablation eval | ✅ DONE |

Chi tiết task-by-task xem `docs/AI1_PROGRESS_TRACKER.md` và `docs/AI2_PROGRESS_TRACKER.md`.
