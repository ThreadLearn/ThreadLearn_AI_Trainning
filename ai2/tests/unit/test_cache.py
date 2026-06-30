"""
AI2-07: Unit tests for cache.py (Redis caching layer).
Run: pytest ai2/tests/test_cache.py -v

Strategy: mock Redis client — không cần Redis server thật khi chạy tests.
Tests:
    test_make_cache_key_deterministic   — cùng input → cùng key
    test_make_cache_key_different       — khác code → khác key
    test_make_cache_key_language_diff   — cùng code, khác language → khác key
    test_make_cache_key_format          — key có prefix "ai2:analysis:"
    test_get_cached_miss                — Redis trả None → get_cached trả None
    test_get_cached_hit                 — Redis có data → trả AnalyzeResponse, cached=True
    test_get_cached_redis_down          — Redis raise exception → trả None (graceful)
    test_set_cached_success             — lưu thành công → trả True
    test_set_cached_redis_down          — Redis down → trả False (graceful)
    test_invalidate_existing_key        — xóa key tồn tại → True
    test_invalidate_missing_key         — xóa key không tồn tại → False
"""

import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from cache import make_cache_key, get_cached, set_cached, invalidate
from schemas import AnalyzeResponse, Issue, DocUsed

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_RESPONSE = AnalyzeResponse(
    user_id="u-001",
    language="javascript",
    issues=[
        Issue(
            line_range="1-5",
            severity="high",
            description="Race condition detected",
            fix="Use Promise.all",
        )
    ],
    docs_used=[
        DocUsed(id="js-001", title="Promise.all Pattern", category="patterns")
    ],
    cached=False,
)

SAMPLE_CODE = "setTimeout(() => { x++; }, 100);"
SAMPLE_LANG = "javascript"


# ---------------------------------------------------------------------------
# make_cache_key tests
# ---------------------------------------------------------------------------

def test_make_cache_key_deterministic():
    """Cùng input → cùng key mọi lần gọi."""
    k1 = make_cache_key(SAMPLE_CODE, SAMPLE_LANG)
    k2 = make_cache_key(SAMPLE_CODE, SAMPLE_LANG)
    assert k1 == k2


def test_make_cache_key_different():
    """Khác code → khác key."""
    k1 = make_cache_key("code_a", SAMPLE_LANG)
    k2 = make_cache_key("code_b", SAMPLE_LANG)
    assert k1 != k2


def test_make_cache_key_language_diff():
    """Cùng code, khác language → khác key."""
    k1 = make_cache_key(SAMPLE_CODE, "javascript")
    k2 = make_cache_key(SAMPLE_CODE, "typescript")
    assert k1 != k2


def test_make_cache_key_format():
    """Key phải bắt đầu bằng 'ai2:analysis:' và có SHA256 (64 hex chars)."""
    key = make_cache_key(SAMPLE_CODE, SAMPLE_LANG)
    assert key.startswith("ai2:analysis:")
    hex_part = key.replace("ai2:analysis:", "")
    assert len(hex_part) == 64
    assert all(c in "0123456789abcdef" for c in hex_part)


# ---------------------------------------------------------------------------
# get_cached tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_cached_miss():
    """Redis trả None (cache miss) → get_cached trả None."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=None)
    mock_client.aclose = AsyncMock()

    with patch("cache.get_redis_client", return_value=mock_client):
        result = await get_cached(SAMPLE_CODE, SAMPLE_LANG)

    assert result is None


@pytest.mark.asyncio
async def test_get_cached_hit():
    """Redis có data → trả AnalyzeResponse với cached=True."""
    payload = SAMPLE_RESPONSE.model_dump()
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=json.dumps(payload))
    mock_client.aclose = AsyncMock()

    with patch("cache.get_redis_client", return_value=mock_client):
        result = await get_cached(SAMPLE_CODE, SAMPLE_LANG)

    assert result is not None
    assert result.cached is True
    assert len(result.issues) == 1
    assert result.issues[0].severity == "high"


@pytest.mark.asyncio
async def test_get_cached_redis_down():
    """Redis raise exception → trả None (graceful degradation)."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=ConnectionError("Redis down"))
    mock_client.aclose = AsyncMock()

    with patch("cache.get_redis_client", return_value=mock_client):
        result = await get_cached(SAMPLE_CODE, SAMPLE_LANG)

    assert result is None   # không crash, trả None


# ---------------------------------------------------------------------------
# set_cached tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_set_cached_success():
    """Lưu thành công → trả True."""
    mock_client = AsyncMock()
    mock_client.setex = AsyncMock(return_value=True)
    mock_client.aclose = AsyncMock()

    with patch("cache.get_redis_client", return_value=mock_client):
        result = await set_cached(SAMPLE_CODE, SAMPLE_LANG, SAMPLE_RESPONSE)

    assert result is True
    # Kiểm tra setex được gọi với đúng TTL
    mock_client.setex.assert_called_once()
    args = mock_client.setex.call_args[0]
    assert args[1] == 86400   # TTL 24h


@pytest.mark.asyncio
async def test_set_cached_redis_down():
    """Redis down → trả False (graceful), không crash."""
    mock_client = AsyncMock()
    mock_client.setex = AsyncMock(side_effect=ConnectionError("Redis down"))
    mock_client.aclose = AsyncMock()

    with patch("cache.get_redis_client", return_value=mock_client):
        result = await set_cached(SAMPLE_CODE, SAMPLE_LANG, SAMPLE_RESPONSE)

    assert result is False


# ---------------------------------------------------------------------------
# invalidate tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invalidate_existing_key():
    """Xóa key tồn tại → True."""
    mock_client = AsyncMock()
    mock_client.delete = AsyncMock(return_value=1)   # 1 key bị xóa
    mock_client.aclose = AsyncMock()

    with patch("cache.get_redis_client", return_value=mock_client):
        result = await invalidate(SAMPLE_CODE, SAMPLE_LANG)

    assert result is True


@pytest.mark.asyncio
async def test_invalidate_missing_key():
    """Xóa key không tồn tại → False."""
    mock_client = AsyncMock()
    mock_client.delete = AsyncMock(return_value=0)   # 0 key bị xóa
    mock_client.aclose = AsyncMock()

    with patch("cache.get_redis_client", return_value=mock_client):
        result = await invalidate(SAMPLE_CODE, SAMPLE_LANG)

    assert result is False
