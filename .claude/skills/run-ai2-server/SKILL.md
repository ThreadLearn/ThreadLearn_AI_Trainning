---
name: run-ai2-server
description: Run, start, launch, smoke test, screenshot, verify, check the AI2 FastAPI server (ThreadLearn race-condition detection microservice). Drives the server with curl. Use for confirming changes work, verifying endpoints, or running the full smoke test.
---

# run-ai2-server

FastAPI server (`ai2/server/main.py`) served on port 8001. Three endpoints: `/health` (public), `POST /api/v1/ai/analyze` (JWT), `GET /api/v1/ai/history/{user_id}` (JWT). Driven with `curl` + a smoke shell script. No GUI — pure HTTP.

Paths below are relative to `ai2/`.

---

## Prerequisites

Python 3.13+. Install deps once:

```bash
cd ai2/server
pip install fastapi uvicorn python-dotenv rank-bm25 openai httpx redis motor pymongo "python-jose[cryptography]"
```

Optional services (server starts without them — graceful degradation):
- Redis on `localhost:6379` (cache layer)
- MongoDB on `localhost:27017` (history storage)

Docker shortcut for both:
```bash
docker run -d -p 6379:6379 redis:alpine
docker run -d -p 27017:27017 mongo:7
```

---

## Config

Edit `ai2/server/.env` before starting. Minimum required:

```
LLM_PROVIDER=mock        # mock | openai | ollama
JWT_SECRET=              # must match Node.js backend; empty string OK for local dev
```

`config.py` loads `.env` at import time — env vars set in the shell AFTER Python starts are ignored. Always edit the `.env` file.

---

## Run (agent path — smoke test)

The smoke script launches the server, runs 3 real HTTP calls, asserts responses, then stops. This is the primary way an agent verifies the server works.

```bash
cd ai2/server
bash ../.claude/skills/run-ai2-server/smoke.sh
```

Expected output (all checks pass):
```
[smoke] GET /health           ✓ health OK (retriever_docs=2050)
[smoke] JWT generated (sub=smoke-user)
[smoke] POST /api/v1/ai/analyze   ✓ analyze OK (issues=1)
[smoke] GET /api/v1/ai/history/smoke-user   ✓ history OK (total=1)
[smoke] ALL CHECKS PASS ✓
```

Pass `--keep` to leave the server running after the test:
```bash
bash ../.claude/skills/run-ai2-server/smoke.sh --keep
```

---

## Run (human path)

```bash
cd ai2/server
uvicorn main:app --reload --port 8001
# Swagger UI: http://localhost:8001/docs
```

`--reload` is useless in headless/agent contexts. Use the smoke script instead.

---

## Manual curl calls

Generate a JWT (Python, from `ai2/server/`):

```bash
python -c "
from jose import jwt; import time
from config import JWT_SECRET
token = jwt.encode({'sub':'test-user','exp':int(time.time())+3600}, JWT_SECRET, algorithm='HS256')
print(token)
"
```

Then use `$TOKEN` in requests:

```bash
# Health (no JWT)
curl -s http://localhost:8001/health

# Analyze
curl -s -X POST http://localhost:8001/api/v1/ai/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"for(var i=0;i<3;i++){setTimeout(function(){console.log(i)},1000);}","language":"javascript","user_id":"test-user"}'

# History (paginated)
curl -s "http://localhost:8001/api/v1/ai/history/test-user?page=1&limit=5" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Tests

```bash
cd ai2/server
pytest ../tests/unit/ -v
```

85 pass, 5 fail (`test_race_detector.py` Python-pattern cases — `global_var_thread`, `shared_list_no_lock`, `missing_join`, `singleton_lazy_init`, `counter_no_atomic_python` — pre-existing detector gaps for the Python language path, unrelated to the JS/server code this skill drives).

---

## Gotchas

- **`JWT_SECRET` loaded at import time.** `config.py` calls `load_dotenv()` the moment it's imported. Shell env vars set after the process starts have no effect. Always put `JWT_SECRET` in `ai2/server/.env`.

- **Port 10048 / WINERROR 10048 on Windows.** "Only one usage of each socket address" — port 8001 already in use. Find and kill the old process: `netstat -ano | findstr :8001`, then `taskkill /PID <pid> /F`.

- **Mock LLM returns generic issue.** `LLM_PROVIDER=mock` always returns one hardcoded `Issue` regardless of input. Tests pass; real detection requires `openai` or `ollama`.

- **MongoDB/Redis connection failures are silent.** Server starts fine with no MongoDB or Redis. History returns empty; cache is bypassed. Check logs for `[Errno 111] Connection refused` if you expect persistence to work.

- **Semaphore check pattern.** `_llm_semaphore._value` is private — works on CPython 3.13 but is technically internal. Returns 429 only when all 3 slots are occupied.

- **`asyncio.timeout` Python 3.11+.** Do not backport to 3.10 — use `asyncio.wait_for` instead.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `401 Token không hợp lệ` | JWT signed with wrong secret. Generate token with the same `JWT_SECRET` that's in `.env`. |
| `retriever_docs: 0` | `knowledge-base/knowledge_base.json` not found. Run from `ai2/server/` or check `KNOWLEDGE_BASE_PATH` in `config.py`. |
| Server hangs at startup | MongoDB/Redis unreachable AND `ensure_indexes()` blocking. Kill and check DB services. |
| `ModuleNotFoundError: motor` | `pip install motor pymongo` in the correct Python env. |
