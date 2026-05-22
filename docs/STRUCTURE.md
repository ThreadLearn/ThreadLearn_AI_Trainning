# ThreadLearn AI — Project Structure

```
ThreadLearn-AI-Trainning/
├── ai1/                          # AI1 — Ân: Fine-tune & AST
│   ├── data/
│   │   ├── raw/                  # raw_dataset.json (500-1000 cặp JS+Python)
│   │   └── processed/            # train.jsonl + eval.jsonl (split 90/10)
│   ├── training/                 # QLoRA training notebooks & scripts
│   ├── model/                    # exported SafeTensors (gitignored nếu >100MB)
│   ├── modules/
│   │   ├── ast_preprocessor.py   # AI1-03: parse AST, stripComments, extractFunctions
│   │   └── output_parser.py      # AI1-08: parse LLM raw output → {code, explanation}
│   └── tests/
│       └── test_ast.py           # unit tests cho ast_preprocessor (20 cases)
│
├── ai2/                          # AI2 — Trung: Serving, RAG & Race Condition
│   ├── knowledge-base/
│   │   ├── knowledge_base.json   # 250 docs concurrent JS patterns (AI2-01 DONE)
│   │   └── KNOWLEDGE_BASE_OVERVIEW.md  # schema, category breakdown, usage guide
│   ├── server/
│   │   ├── main.py               # AI2-05: FastAPI app, routes, JWT middleware
│   │   ├── bm25_module.py        # AI2-02: BM25 indexer + search (in-memory)
│   │   ├── race_detector.py      # AI2-03: rule-based detector, 10 RC patterns
│   │   ├── report_formatter.py   # AI2-04: format RC output → JSON {severity, fix}
│   │   ├── rag_pipeline.py       # AI2-06: RAG flow code→AST→BM25→LLM→response
│   │   ├── cache.py              # AI2-07: Redis cache SHA256 key, TTL 24h
│   │   ├── db.py                 # AI2-09: MongoDB motor, ai_analysis_history
│   │   ├── llm_client.py         # AI2-08: LLMClient ABC → OpenAIClient/OllamaClient
│   │   ├── config.py             # env vars: API keys, URLs, LLM provider
│   │   └── requirements.txt      # Python dependencies for ai2/server
│   └── tests/
│       ├── test_bm25.py          # AI2-02: 10 query relevance tests
│       ├── test_race_detector.py # AI2-03: 15 positive + 10 negative cases
│       └── test_rag_pipeline.py  # AI2-06: E2E 5 sample analysis
│
├── shared/
│   └── README.md                 # cross-team import docs, delivery schedule
│
├── docs/
│   ├── STRUCTURE.md              # this file
│   └── AI2_PROGRESS_TRACKER.md  # Trung's task tracker (10 tasks, checkpoints, risks)
│
├── .gitignore
└── README.md
```

---

## Folder Descriptions

### `ai1/data/raw/`
Raw dataset: cặp code đơn luồng → đa luồng thu thập từ GitHub, Kaggle, viết tay.
Target: 500-1000 cặp JS + Python. Output: `raw_dataset.json`.

### `ai1/data/processed/`
Dataset sau khi format sang JSONL chuẩn SFTTrainer.
Output: `train.jsonl` (90%) + `eval.jsonl` (10%).

### `ai1/training/`
Notebooks và scripts cho QLoRA fine-tune Qwen2.5-Coder-1.5B trên Kaggle/RunPod.
Chứa: training config, hyperparameters, loss curve screenshots.

### `ai1/model/`
Exported model sau fine-tune. SafeTensors (~3-4GB) **gitignored** — chia sẻ qua HuggingFace Hub / Google Drive link.

### `ai1/modules/`
Shared Python modules do AI1 viết, AI2 import trực tiếp.
- `ast_preprocessor.py` — AI2 dùng cho race_detector và rag_pipeline
- `output_parser.py` — AI2 dùng khi swap sang Ollama (Iter 3)

### `ai2/knowledge-base/`
Nguồn dữ liệu RAG: 250 tài liệu JavaScript concurrent patterns.
BM25 index được build từ file này mỗi lần server start.
**Không sửa trực tiếp** — thêm doc mới bằng cách append vào `knowledge_base.json` với id tiếp theo (js-251...).

### `ai2/server/`
FastAPI microservice — đây là core của AI2.
Import chain: `main.py` → `rag_pipeline.py` → `bm25_module.py` + `llm_client.py` + `race_detector.py` → `report_formatter.py`.

### `ai2/tests/`
Pytest test suite. Chạy từ root:
```bash
cd ThreadLearn-AI-Trainning
pytest ai2/tests/ -v
```

### `shared/`
Không chứa code — chỉ chứa docs về cross-team dependencies và import pattern.
Khi AI1 deliver module, AI2 import thẳng từ `ai1/modules/`.

### `docs/`
Tài liệu kỹ thuật dùng chung cả team.

---

## Key Files Quick Reference

| File | Task | Status |
|------|------|--------|
| `ai2/knowledge-base/knowledge_base.json` | AI2-01 | ✅ DONE |
| `ai2/server/bm25_module.py` | AI2-02 | 🔄 In Progress |
| `ai2/server/race_detector.py` | AI2-03 | 🚫 Blocked (AI1-03) |
| `ai2/server/report_formatter.py` | AI2-04 | ⏳ Pending |
| `ai2/server/main.py` | AI2-05 | ⏳ Pending |
| `ai2/server/rag_pipeline.py` | AI2-06 | ⏳ Pending (CP3 critical) |
| `ai2/server/cache.py` | AI2-07 | ⏳ Pending |
| `ai2/server/llm_client.py` | AI2-08 | 🚫 Blocked (AI1-07) |
| `ai2/server/db.py` | AI2-09 | ⏳ Pending |
| `ai1/modules/ast_preprocessor.py` | AI1-03 | ⏳ Pending |
| `ai1/modules/output_parser.py` | AI1-08 | ⏳ Pending |
