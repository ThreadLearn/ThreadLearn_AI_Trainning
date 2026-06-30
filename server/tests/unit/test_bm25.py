"""
AI2-02: Unit tests for bm25_module
Tests: 10 relevance queries + tokenizer + edge cases + build performance
Run: pytest server/tests/test_bm25.py -v
"""

import os
import time
import pytest

from bm25_module import tokenize, BM25Retriever, load_retriever

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

KB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "knowledge-base", "knowledge_base.json"
)


@pytest.fixture(scope="module")
def retriever():
    """Build retriever once for all tests in module."""
    r = load_retriever(KB_PATH)
    return r


# ---------------------------------------------------------------------------
# Tokenizer tests
# ---------------------------------------------------------------------------

def test_tokenize_camel_case():
    tokens = tokenize("fetchAllUsers")
    assert "fetch" in tokens
    assert "all" in tokens
    assert "users" in tokens


def test_tokenize_snake_case():
    tokens = tokenize("shared_array_buffer")
    assert "shared" in tokens
    assert "array" in tokens
    assert "buffer" in tokens


def test_tokenize_removes_stopwords():
    tokens = tokenize("the Promise is a pattern for async")
    assert "the" not in tokens
    assert "is" not in tokens
    assert "a" not in tokens
    assert "promise" in tokens
    assert "pattern" in tokens
    assert "async" in tokens


def test_tokenize_js_api():
    tokens = tokenize("Promise.all parallel execution")
    assert "promise" in tokens
    assert "parallel" in tokens
    assert "execution" in tokens


# ---------------------------------------------------------------------------
# Index build tests
# ---------------------------------------------------------------------------

def test_build_time_under_2s(retriever):
    """Index over 2050 docs must build in <2s."""
    assert retriever.build_time_ms < 2000, (
        f"Build too slow: {retriever.build_time_ms:.1f}ms (limit: 2000ms)"
    )


def test_doc_count(retriever):
    assert retriever.doc_count == 2050


# ---------------------------------------------------------------------------
# Relevance query tests (10 queries)
# ---------------------------------------------------------------------------

def test_query_promise_all(retriever):
    """Query about Promise.all should return parallel execution docs."""
    results = retriever.search("Promise.all parallel fetch", top_k=3)
    assert len(results) > 0
    titles = [r["title"].lower() for r in results]
    assert any("promise" in t or "parallel" in t for t in titles), (
        f"Expected Promise/parallel in titles, got: {titles}"
    )


def test_query_web_workers(retriever):
    """Query about Web Workers should return worker thread docs."""
    results = retriever.search("Web Worker thread postMessage", top_k=3)
    assert len(results) > 0
    titles = [r["title"].lower() for r in results]
    assert any("worker" in t for t in titles), (
        f"Expected worker in titles, got: {titles}"
    )


def test_query_shared_array_buffer(retriever):
    """Query about SharedArrayBuffer should return memory-sharing docs."""
    results = retriever.search("SharedArrayBuffer Atomics shared memory", top_k=3)
    assert len(results) > 0
    titles = [r["title"].lower() for r in results]
    assert any("shared" in t or "atomic" in t or "buffer" in t for t in titles), (
        f"Expected shared/atomic/buffer in titles, got: {titles}"
    )


def test_query_race_condition(retriever):
    """Query about race conditions should return race-condition category docs."""
    results = retriever.search("race condition shared variable setTimeout", top_k=3)
    assert len(results) > 0
    categories = [r["category"] for r in results]
    assert any(c == "race-conditions" for c in categories), (
        f"Expected race-conditions category, got: {categories}"
    )


def test_query_async_await(retriever):
    """Query about async/await patterns should return relevant docs."""
    results = retriever.search("async await sequential concurrent", top_k=3)
    assert len(results) > 0
    assert all("id" in r and "title" in r and "content" in r for r in results)


def test_query_mutex_lock(retriever):
    """Query about mutex/locking should return synchronization docs."""
    results = retriever.search("mutex lock semaphore resource", top_k=3)
    assert len(results) > 0
    combined = " ".join(r["title"].lower() + r["content"].lower() for r in results)
    assert any(kw in combined for kw in ["mutex", "lock", "semaphore"]), (
        "Expected mutex/lock/semaphore in results"
    )


def test_query_anti_pattern_callback_hell(retriever):
    """Query about callback hell should return anti-pattern docs."""
    results = retriever.search("callback hell nested pyramid", top_k=3)
    assert len(results) > 0
    categories = [r["category"] for r in results]
    assert any(c == "anti-patterns" for c in categories), (
        f"Expected anti-patterns category, got: {categories}"
    )


def test_query_abort_controller(retriever):
    """Query about AbortController should return cancellation docs."""
    results = retriever.search("AbortController cancel fetch request", top_k=3)
    assert len(results) > 0
    combined = " ".join(r["title"].lower() for r in results)
    assert any(kw in combined for kw in ["abort", "cancel"]), (
        f"Expected abort/cancel in titles, got: {combined}"
    )


def test_query_top_k_limit(retriever):
    """Search with top_k=3 must return at most 3 results."""
    results = retriever.search("concurrent programming", top_k=3)
    assert len(results) <= 3


def test_query_empty_returns_empty(retriever):
    """Empty query should return empty list."""
    results = retriever.search("", top_k=3)
    assert results == []


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------

def test_search_before_build_raises():
    """Calling search on unbuilt retriever should raise RuntimeError."""
    r = BM25Retriever()
    with pytest.raises(RuntimeError, match="Index not built"):
        r.search("test query")


def test_build_with_minimal_docs():
    """Retriever should build and search on a small custom doc list without error."""
    docs = [
        {"id": "t-001", "title": "Promise all pattern", "content": "Use Promise.all to run tasks in parallel concurrent execution.", "category": "patterns"},
        {"id": "t-002", "title": "setTimeout race condition", "content": "Shared variable modified in setTimeout causes race condition bug.", "category": "race-conditions"},
        {"id": "t-003", "title": "async await sequential", "content": "Sequential execution with await waits for each operation.", "category": "patterns"},
        {"id": "t-004", "title": "Worker thread offload", "content": "Worker threads offload CPU-intensive work from main thread.", "category": "patterns"},
    ]
    r = BM25Retriever()
    r.build(docs)
    assert r.doc_count == 4
    # race condition query should rank t-002 first (unique terms: shared, race, condition)
    results = r.search("race condition shared variable", top_k=1)
    assert len(results) == 1
    assert results[0]["id"] == "t-002"
