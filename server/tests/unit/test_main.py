"""
AI2-05: Integration tests for FastAPI routes.
Run: pytest server/tests/test_main.py -v

Tests:
    test_health_ok              — GET /health → 200
    test_analyze_no_auth        — POST /analyze sans token → 401
    test_analyze_with_jwt       — POST /analyze avec valid JWT → 200 + valid schema
    test_history_own_user       — GET /history/<own_id> → 200 + empty list
    test_history_other_user     — GET /history/<other_id> → 403
"""

import os
from datetime import datetime, timezone, timedelta

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from unittest.mock import AsyncMock, patch

TEST_SECRET = "test-secret-for-pytest"
os.environ["JWT_SECRET"] = TEST_SECRET
os.environ["LLM_PROVIDER"] = "mock"

from main import app   # noqa: E402
import auth            # noqa: E402
import cache           # noqa: E402

# Đảm bảo auth.py dùng TEST_SECRET bất kể config.py đã load .env trước
auth.JWT_SECRET = TEST_SECRET



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_token(user_id: str, secret: str = TEST_SECRET, expired: bool = False) -> str:
    """Tạo JWT hợp lệ cho test. expired=True tạo token đã hết hạn."""
    now = datetime.now(timezone.utc)
    exp = now - timedelta(hours=1) if expired else now + timedelta(hours=1)
    payload = {"sub": user_id, "exp": exp}
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture()
def client():
    """Function-scoped TestClient. Force mock LLM + no-op Redis + no-op MongoDB."""
    import llm_client
    import cache as _cache
    import db as _db

    async def _miss(*args, **kwargs): return None
    async def _ok(*args, **kwargs): return True
    async def _save(*args, **kwargs): return "507f1f77bcf86cd799439011"
    async def _history(*args, **kwargs): return [], 0

    orig_provider = llm_client.LLM_PROVIDER
    llm_client.LLM_PROVIDER = "mock"
    _cache.get_cached = _miss
    _cache.set_cached = _ok
    _db.save_analysis = _save       # no-op MongoDB write
    _db.get_history = _history      # no-op MongoDB read

    with TestClient(app) as c:
        yield c

    llm_client.LLM_PROVIDER = orig_provider


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def test_health_ok(client):
    """GET /health phải trả 200 và retriever_docs > 0."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["retriever_docs"] > 0


# ---------------------------------------------------------------------------
# POST /api/v1/ai/analyze
# ---------------------------------------------------------------------------

def test_analyze_no_auth(client):
    """Không có Authorization header → 401 (HTTPBearer reject khi thiếu token)."""
    resp = client.post(
        "/api/v1/ai/analyze",
        json={"code": "setTimeout(() => {}, 0);", "language": "javascript", "user_id": "u1"},
    )
    assert resp.status_code == 401


def test_analyze_invalid_token(client):
    """Token sai secret → 401."""
    token = _make_token("u1", secret="wrong-secret")
    resp = client.post(
        "/api/v1/ai/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json={"code": "setTimeout(() => {}, 0);", "language": "javascript", "user_id": "u1"},
    )
    assert resp.status_code == 401


def test_analyze_expired_token(client):
    """Token hết hạn → 401."""
    token = _make_token("u1", expired=True)
    resp = client.post(
        "/api/v1/ai/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json={"code": "setTimeout(() => {}, 0);", "language": "javascript", "user_id": "u1"},
    )
    assert resp.status_code == 401


def test_analyze_with_valid_jwt(client):
    """JWT hợp lệ → 200 + response schema đúng."""
    token = _make_token("user-123")
    resp = client.post(
        "/api/v1/ai/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "code": "let x = 0; setTimeout(() => { x++; }, 100);",
            "language": "javascript",
            "user_id": "user-123",
        },
    )
    assert resp.status_code == 200
    data = resp.json()

    # Kiểm tra shape của response
    assert "user_id" in data
    assert "language" in data
    assert "issues" in data
    assert "docs_used" in data
    assert "cached" in data
    assert isinstance(data["issues"], list)
    assert isinstance(data["docs_used"], list)
    assert data["cached"] is False

    # Mock LLM luôn trả 1 issue
    assert len(data["issues"]) >= 1
    issue = data["issues"][0]
    assert "line_range" in issue
    assert issue["severity"] in ("high", "medium", "low")
    assert "description" in issue
    assert "fix" in issue


# ---------------------------------------------------------------------------
# GET /api/v1/ai/history/{user_id}
# ---------------------------------------------------------------------------

def test_history_own_user(client):
    """User xem lịch sử của chính mình → 200 + empty list."""
    token = _make_token("user-abc")
    resp = client.get(
        "/api/v1/ai/history/user-abc",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == "user-abc"
    assert data["analyses"] == []
    assert data["total"] == 0


def test_history_other_user(client):
    """User xem lịch sử của người khác → 403."""
    token = _make_token("user-abc")
    resp = client.get(
        "/api/v1/ai/history/user-xyz",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_history_response_has_pagination_fields(client):
    """GET /history → response có page, limit, total fields."""
    token = _make_token("user-abc")
    resp = client.get(
        "/api/v1/ai/history/user-abc",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "page" in data
    assert "limit" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["limit"] == 20


def test_history_custom_pagination(client):
    """GET /history?page=2&limit=5 → pagination params được truyền đúng."""
    token = _make_token("user-abc")
    resp = client.get(
        "/api/v1/ai/history/user-abc?page=2&limit=5",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 2
    assert data["limit"] == 5


def test_analyze_saves_to_mongodb(client):
    """POST /analyze thành công → db.save_analysis được gọi."""
    import db as _db
    calls = []

    async def _capture_save(*args, **kwargs):
        calls.append(kwargs if kwargs else args)
        return "507f1f77bcf86cd799439011"

    _db.save_analysis = _capture_save

    token = _make_token("user-123")
    resp = client.post(
        "/api/v1/ai/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "code": "let x = 0; setTimeout(() => { x++; }, 100);",
            "language": "javascript",
            "user_id": "user-123",
        },
    )
    assert resp.status_code == 200
    assert len(calls) == 1   # save_analysis được gọi đúng 1 lần
