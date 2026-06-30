"""
AI2-09: MongoDB persistence layer — lưu và truy xuất lịch sử phân tích.

Collection: ai_analysis_history
Index: (user_id ASC, created_at DESC) — pagination hiệu quả

Graceful degradation: mọi exception → không crash server.
"""

from datetime import datetime, timezone
from typing import Optional

import motor.motor_asyncio

from config import MONGODB_URL

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

_DB_NAME = "threadlearn_ai"
_COLLECTION = "ai_analysis_history"

_client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None


def get_collection() -> motor.motor_asyncio.AsyncIOMotorCollection:
    """
    Trả về Motor collection. Tạo client nếu chưa có.
    Motor tự pool connection — không cần close thủ công.
    """
    global _client
    if _client is None:
        _client = motor.motor_asyncio.AsyncIOMotorClient(
            MONGODB_URL,
            serverSelectionTimeoutMS=2000,   # fail fast khi Mongo không có
            connectTimeoutMS=2000,
        )
    return _client[_DB_NAME][_COLLECTION]


async def ensure_indexes() -> None:
    """
    Tạo compound index (user_id, created_at DESC) nếu chưa có.
    Gọi một lần lúc server startup trong lifespan.
    """
    try:
        col = get_collection()
        await col.create_index(
            [("user_id", 1), ("created_at", -1)],
            background=True,
            name="user_history_idx",
        )
    except Exception:
        pass   # index creation failure không crash server


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def save_analysis(
    user_id: str,
    input_code: str,
    language: str,
    issues: list,
    docs_used: list,
    model: str,
    cached: bool,
) -> Optional[str]:
    """
    Lưu một bản phân tích vào MongoDB.

    Returns:
        str ObjectId nếu thành công, None nếu Mongo down.
    """
    doc = {
        "user_id": user_id,
        "input_code": input_code,
        "language": language,
        "issues": issues,
        "docs_used": docs_used,
        "issues_count": len(issues),
        "model": model,
        "cached": cached,
        "created_at": datetime.now(timezone.utc),
    }
    try:
        col = get_collection()
        result = await col.insert_one(doc)
        return str(result.inserted_id)
    except Exception:
        return None


async def get_history(
    user_id: str,
    page: int = 1,
    limit: int = 20,
) -> tuple[list, int]:
    """
    Truy vấn lịch sử phân tích của user, sắp xếp mới nhất trước.

    Returns:
        (records, total_count)

    Graceful degradation: Mongo down → trả ([], 0).
    """
    try:
        col = get_collection()
        skip = (page - 1) * limit

        total = await col.count_documents({"user_id": user_id})

        cursor = col.find(
            {"user_id": user_id},
            projection={"_id": 1, "language": 1, "issues_count": 1, "created_at": 1},
        ).sort("created_at", -1).skip(skip).limit(limit)

        records = []
        async for doc in cursor:
            created = doc["created_at"]
            records.append({
                "analysis_id": str(doc["_id"]),
                "language": doc.get("language", "javascript"),
                "issues_count": doc.get("issues_count", 0),
                "created_at": created.isoformat() if isinstance(created, datetime) else str(created),
            })

        return records, total

    except Exception:
        return [], 0
