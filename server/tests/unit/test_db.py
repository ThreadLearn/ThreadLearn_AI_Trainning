"""
AI2-09: Tests for MongoDB persistence layer (db.py).

Tests dùng mock để không cần MongoDB thật khi chạy CI.
Cách chạy: pytest server/tests/test_db.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_issues():
    return [{"line_range": "1-5", "severity": "high", "description": "Test", "fix": "Fix it"}]

def _make_docs():
    return [{"id": "js-001", "title": "Promise", "category": "patterns"}]


# ---------------------------------------------------------------------------
# make_cache_key — key format tests (db không có cache key nhưng test save/get)
# ---------------------------------------------------------------------------

class TestSaveAnalysis:
    """db.save_analysis() — lưu document vào MongoDB."""

    @pytest.mark.asyncio
    async def test_save_returns_object_id_string(self):
        """Lưu thành công → trả ObjectId string."""
        from bson import ObjectId
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()

        mock_col = AsyncMock()
        mock_col.insert_one = AsyncMock(return_value=mock_result)

        with patch("db.get_collection", return_value=mock_col):
            import db
            result = await db.save_analysis(
                user_id="u1",
                input_code="setTimeout(() => {}, 0);",
                language="javascript",
                issues=_make_issues(),
                docs_used=_make_docs(),
                model="mock",
                cached=False,
            )

        assert result is not None
        assert isinstance(result, str)
        assert len(result) == 24   # ObjectId hex length

    @pytest.mark.asyncio
    async def test_save_mongo_down_returns_none(self):
        """MongoDB down → trả None, không raise."""
        mock_col = AsyncMock()
        mock_col.insert_one = AsyncMock(side_effect=Exception("connection refused"))

        with patch("db.get_collection", return_value=mock_col):
            import db
            result = await db.save_analysis(
                user_id="u1",
                input_code="code",
                language="javascript",
                issues=[],
                docs_used=[],
                model="mock",
                cached=False,
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_save_document_contains_correct_fields(self):
        """Document được insert phải có đủ fields."""
        from bson import ObjectId
        mock_result = MagicMock()
        mock_result.inserted_id = ObjectId()

        inserted_doc = {}
        async def capture_insert(doc):
            inserted_doc.update(doc)
            return mock_result

        mock_col = AsyncMock()
        mock_col.insert_one = AsyncMock(side_effect=capture_insert)

        with patch("db.get_collection", return_value=mock_col):
            import db
            await db.save_analysis(
                user_id="user-abc",
                input_code="let x = 0;",
                language="javascript",
                issues=_make_issues(),
                docs_used=_make_docs(),
                model="openai",
                cached=True,
            )

        assert inserted_doc["user_id"] == "user-abc"
        assert inserted_doc["language"] == "javascript"
        assert inserted_doc["issues_count"] == 1
        assert inserted_doc["model"] == "openai"
        assert inserted_doc["cached"] is True
        assert "created_at" in inserted_doc


class TestGetHistory:
    """db.get_history() — truy vấn lịch sử phân tích."""

    @pytest.mark.asyncio
    async def test_get_history_returns_records_and_total(self):
        """Query thành công → (records, total)."""
        from bson import ObjectId

        fake_docs = [
            {
                "_id": ObjectId(),
                "language": "javascript",
                "issues_count": 2,
                "created_at": datetime(2026, 5, 31, 10, 0, 0, tzinfo=timezone.utc),
            },
            {
                "_id": ObjectId(),
                "language": "javascript",
                "issues_count": 0,
                "created_at": datetime(2026, 5, 30, 9, 0, 0, tzinfo=timezone.utc),
            },
        ]

        # Motor cursor mock
        async def fake_cursor_iter(self_):
            for doc in fake_docs:
                yield doc

        mock_cursor = MagicMock()
        mock_cursor.__aiter__ = fake_cursor_iter
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)

        mock_col = AsyncMock()
        mock_col.count_documents = AsyncMock(return_value=2)
        mock_col.find = MagicMock(return_value=mock_cursor)

        with patch("db.get_collection", return_value=mock_col):
            import db
            records, total = await db.get_history("user-abc", page=1, limit=20)

        assert total == 2
        assert len(records) == 2
        assert records[0]["issues_count"] == 2
        assert records[0]["language"] == "javascript"
        assert "analysis_id" in records[0]
        assert "created_at" in records[0]

    @pytest.mark.asyncio
    async def test_get_history_empty_user(self):
        """User không có lịch sử → ([], 0)."""
        async def fake_cursor_iter(self_):
            return
            yield  # noqa: unreachable — makes this an async generator

        mock_cursor = MagicMock()
        mock_cursor.__aiter__ = fake_cursor_iter
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)

        mock_col = AsyncMock()
        mock_col.count_documents = AsyncMock(return_value=0)
        mock_col.find = MagicMock(return_value=mock_cursor)

        with patch("db.get_collection", return_value=mock_col):
            import db
            records, total = await db.get_history("nobody", page=1, limit=20)

        assert records == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_history_mongo_down_returns_empty(self):
        """MongoDB down → ([], 0), không raise."""
        mock_col = AsyncMock()
        mock_col.count_documents = AsyncMock(side_effect=Exception("timeout"))

        with patch("db.get_collection", return_value=mock_col):
            import db
            records, total = await db.get_history("u1", page=1, limit=20)

        assert records == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_history_pagination_skip_calculated_correctly(self):
        """page=2, limit=10 → skip=10."""
        async def fake_cursor_iter(self_):
            return
            yield

        mock_cursor = MagicMock()
        mock_cursor.__aiter__ = fake_cursor_iter
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        skip_mock = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = skip_mock
        mock_cursor.limit = MagicMock(return_value=mock_cursor)

        mock_col = AsyncMock()
        mock_col.count_documents = AsyncMock(return_value=25)
        mock_col.find = MagicMock(return_value=mock_cursor)

        with patch("db.get_collection", return_value=mock_col):
            import db
            await db.get_history("u1", page=2, limit=10)

        skip_mock.assert_called_once_with(10)   # (2-1) * 10 = 10


class TestEnsureIndexes:
    """db.ensure_indexes() — không crash kể cả khi Mongo down."""

    @pytest.mark.asyncio
    async def test_ensure_indexes_success(self):
        mock_col = AsyncMock()
        mock_col.create_index = AsyncMock(return_value="user_history_idx")

        with patch("db.get_collection", return_value=mock_col):
            import db
            await db.ensure_indexes()   # không raise

        mock_col.create_index.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_indexes_mongo_down_no_crash(self):
        mock_col = AsyncMock()
        mock_col.create_index = AsyncMock(side_effect=Exception("connection refused"))

        with patch("db.get_collection", return_value=mock_col):
            import db
            await db.ensure_indexes()   # không raise — graceful
