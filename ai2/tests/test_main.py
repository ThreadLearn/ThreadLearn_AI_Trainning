"""
AI2-05: Integration tests for FastAPI routes.
Run: pytest ai2/tests/test_main.py -v

Tests:
    test_health_ok              — GET /health → 200
    test_analyze_no_auth        — POST /analyze sans token → 401
    test_analyze_with_jwt       — POST /analyze avec valid JWT → 200 + valid schema
    test_history_own_user       — GET /history/<own_id> → 200 + empty list
    test_history_other_user     — GET /history/<other_id> → 403
"""

import sys
import os
from datetime import datetime, timezone, timedelta

import pytest
from fastapi.testclient import TestClient
from jose import jwt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))

# Patch JWT_SECRET trước khi import app
TEST_SECRET = "test-secret-for-pytest"
os.environ["JWT_SECRET"] = TEST_SECRET
os.environ["LLM_PROVIDER"] = "mock"   # Luôn dùng mock trong tests

from main import app  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_token(user_id: str, secret: str = TEST_SECRET, expired: bool = False) -> str:
    """Tạo JWT hợp lệ cho test. expired=True tạo token đã hết hạn."""
    now = datetime.now(timezone.utc)
    exp = now - timedelta(hours=1) if expired else now + timedelta(hours=1)
    payload = {"sub": user_id, "exp": exp}
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture(scope="module")
def client():
    """TestClient với lifespan (load BM25 retriever)."""
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def test_health_ok(client):
    """GET /health phải trả 200 và retriever_docs = 250."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["retriever_docs"] == 250


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
