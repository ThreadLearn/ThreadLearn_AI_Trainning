#!/usr/bin/env bash
# smoke.sh — launch ai2 server, run 3 real HTTP calls, stop server.
# Run from: ai2/server/   (must have .env present or env vars set)
# Usage: bash ../.claude/skills/run-ai2-server/smoke.sh [--keep]
#   --keep : do not kill the server after smoke test (leave it running)
#
# Exit 0 = all checks pass. Exit 1 = any failure.

set -e
KEEP=0
[[ "${1:-}" == "--keep" ]] && KEEP=1

SERVER_DIR="$(cd "$(dirname "$0")/../../../server" && pwd)"
cd "$SERVER_DIR"

# ── 1. Start server in background ──────────────────────────────────────────
echo "[smoke] Starting server on :8001..."
python -m uvicorn main:app --host 0.0.0.0 --port 8001 \
  --log-level warning &
SERVER_PID=$!

cleanup() {
  if [[ $KEEP -eq 0 ]]; then
    echo "[smoke] Stopping server (pid $SERVER_PID)..."
    kill "$SERVER_PID" 2>/dev/null || true
  else
    echo "[smoke] Server left running (pid $SERVER_PID). Kill with: kill $SERVER_PID"
  fi
}
trap cleanup EXIT

# Wait for server to be ready (up to 10s)
for i in $(seq 1 20); do
  curl -sf http://localhost:8001/health >/dev/null 2>&1 && break
  sleep 0.5
done

# ── 2. Health check ─────────────────────────────────────────────────────────
echo "[smoke] GET /health"
HEALTH=$(curl -sf http://localhost:8001/health)
echo "  → $HEALTH"
echo "$HEALTH" | python -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='ok', d"
echo "  ✓ health OK (retriever_docs=$(echo $HEALTH | python -c 'import sys,json; print(json.load(sys.stdin)["retriever_docs"])'))"

# ── 3. Generate JWT (use whatever JWT_SECRET the server loaded) ─────────────
JWT_SECRET_ACTUAL=$(python -c "from config import JWT_SECRET; print(JWT_SECRET)")
TOKEN=$(python -c "
from jose import jwt; import time
print(jwt.encode({'sub':'smoke-user','exp':int(time.time())+600}, '$JWT_SECRET_ACTUAL', algorithm='HS256'))
")
echo "[smoke] JWT generated (sub=smoke-user)"

# ── 4. POST /api/v1/ai/analyze ─────────────────────────────────────────────
echo "[smoke] POST /api/v1/ai/analyze"
ANALYZE=$(curl -sf -X POST http://localhost:8001/api/v1/ai/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"for(var i=0;i<3;i++){setTimeout(function(){console.log(i)},1000);}","language":"javascript","user_id":"smoke-user"}')
echo "  → $(echo $ANALYZE | python -m json.tool --no-ensure-ascii | head -6)"
echo "$ANALYZE" | python -c "import sys,json; d=json.load(sys.stdin); assert 'issues' in d, 'missing issues'"
echo "  ✓ analyze OK (issues=$(echo $ANALYZE | python -c 'import sys,json; print(len(json.load(sys.stdin)["issues"]))'))"

# ── 5. GET /api/v1/ai/history/{user_id} ─────────────────────────────────────
echo "[smoke] GET /api/v1/ai/history/smoke-user"
HIST=$(curl -sf "http://localhost:8001/api/v1/ai/history/smoke-user?page=1&limit=5" \
  -H "Authorization: Bearer $TOKEN")
echo "  → $(echo $HIST | python -m json.tool --no-ensure-ascii | head -5)"
echo "$HIST" | python -c "import sys,json; d=json.load(sys.stdin); assert 'analyses' in d, 'missing analyses'"
echo "  ✓ history OK (total=$(echo $HIST | python -c 'import sys,json; print(json.load(sys.stdin)["total"])'))"

echo ""
echo "[smoke] ALL CHECKS PASS ✓"
