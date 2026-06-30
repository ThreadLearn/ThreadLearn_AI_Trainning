"""
AI2-07: Redis Caching Layer
Key strategy: SHA256(code + language) → đảm bảo cùng code + ngôn ngữ → cùng key.
TTL: 86400s (24h) — kết quả phân tích không đổi trong 24h nếu code không đổi.

Graceful degradation: nếu Redis down → cache miss → vẫn chạy pipeline bình thường.
Server không crash khi Redis không có.
"""

import hashlib
import json
from typing import Optional

import redis.asyncio as aioredis

from config import REDIS_URL
from schemas import AnalyzeResponse

TTL_SECONDS = 86400   # 24 giờ


# ---------------------------------------------------------------------------
# Cache key
# ---------------------------------------------------------------------------

def make_cache_key(code: str, language: str) -> str:
    """
    Tạo cache key từ SHA256(code + "|" + language).

    Tại sao SHA256?
        - Redis key có giới hạn độ dài — code có thể rất dài
        - SHA256 luôn cho key 64 ký tự cố định
        - Collision probability: 1/2^256 ≈ 0 trong thực tế

    Ví dụ:
        make_cache_key("setTimeout(() => {}, 0);", "javascript")
        → "ai2:analysis:a3f2c1..."  (64 hex chars sau prefix)

    Prefix "ai2:analysis:" để namespace, tránh conflict với key khác trong Redis.
    """
    raw = f"{code}|{language}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"ai2:analysis:{digest}"


# ---------------------------------------------------------------------------
# Redis connection
# ---------------------------------------------------------------------------

def get_redis_client() -> aioredis.Redis:
    """
    Tạo async Redis client từ REDIS_URL trong .env.
    Gọi mỗi khi cần — redis.asyncio tự pool connection.

    decode_responses=True → nhận str thay vì bytes (dễ json.loads hơn).
    """
    return aioredis.from_url(
        REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=1,   # fail fast khi Redis không có → graceful degradation
        socket_timeout=1,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def get_cached(code: str, language: str) -> Optional[AnalyzeResponse]:
    """
    Lấy kết quả từ Redis cache.

    Returns:
        AnalyzeResponse nếu cache hit (với cached=True)
        None nếu cache miss hoặc Redis down

    Graceful degradation: bắt mọi Exception → trả None, không raise.
    """
    key = make_cache_key(code, language)
    try:
        client = get_redis_client()
        raw = await client.get(key)
        await client.aclose()

        if raw is None:
            return None   # cache miss

        data = json.loads(raw)
        response = AnalyzeResponse(**data)
        response.cached = True   # đánh dấu là từ cache
        return response

    except Exception:
        # Redis down hoặc lỗi deserialize → cache miss, tiếp tục pipeline
        return None


async def set_cached(code: str, language: str, response: AnalyzeResponse) -> bool:
    """
    Lưu kết quả phân tích vào Redis với TTL 86400s.

    Args:
        code, language: dùng để tạo cache key
        response:       AnalyzeResponse cần cache

    Returns:
        True nếu lưu thành công, False nếu Redis down.

    Graceful degradation: lỗi Redis không ảnh hưởng response trả về client.
    """
    key = make_cache_key(code, language)
    try:
        client = get_redis_client()
        # model_dump() → dict, loại bỏ field cached trước khi lưu
        # (khi đọc ra sẽ set cached=True lại trong get_cached)
        payload = response.model_dump()
        payload["cached"] = False   # lưu trạng thái gốc, get_cached sẽ set True
        await client.setex(key, TTL_SECONDS, json.dumps(payload))
        await client.aclose()
        return True

    except Exception:
        return False


async def invalidate(code: str, language: str) -> bool:
    """
    Xóa cache key (dùng khi cần force re-analyze).
    Trả False nếu key không tồn tại hoặc Redis down.
    """
    key = make_cache_key(code, language)
    try:
        client = get_redis_client()
        deleted = await client.delete(key)
        await client.aclose()
        return deleted > 0
    except Exception:
        return False
