# ThreadLearn AI — Training & Serving

AI subsystem for ThreadLearn: fine-tune a code model (AI1) and serve concurrent programming analysis via RAG (AI2).

## Team

| Role | Engineer | Responsibility |
|------|----------|----------------|
| AI1 | Ân | Fine-tune Qwen2.5-Coder-1.5B on concurrent code dataset |
| AI2 | Trung | FastAPI serving, BM25 RAG pipeline, race condition detection |

## Quick Start

### AI2 Server (Trung)
```bash
cd ai2/server
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### Run Tests
```bash
pytest ai2/tests/ -v
```

## Architecture

```
Frontend (React)
      │  POST /api/v1/ai/analyze
      ▼
[Node.js Backend] — verify JWT →
      │
      ▼
[FastAPI — ai2/server/main.py]
      │
      ├─► Redis Cache (cache.py) — HIT → return <100ms
      │        │ MISS
      ▼        ▼
[AST Preprocessor] ← ai1/modules/ast_preprocessor.py
      │
      ▼
[BM25 Search] (bm25_module.py) — top 3 docs from knowledge_base.json
      │
      ▼
[Build Prompt] → [LLM Call] (llm_client.py) → OpenAI | Ollama
      │
      ├─► [Race Detector] (race_detector.py)
      │
      ▼
[Report Formatter] → save MongoDB (db.py) → set Redis → Response
```

## Docs

- [Project Structure](docs/STRUCTURE.md)
- [AI2 Progress Tracker](docs/AI2_PROGRESS_TRACKER.md)
- [Knowledge Base Overview](ai2/knowledge-base/KNOWLEDGE_BASE_OVERVIEW.md)
- [Shared Module Imports](shared/README.md)
