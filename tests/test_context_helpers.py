"""
Tests for context filtering, memory, and orchestrator helpers.
"""

from adsp.core.context_filter import (
    ConversationContextFilter,
    _extract_json,
    _join_context_blocks,
    _looks_like_follow_up,
    _meaningful_tokens,
    _split_context_blocks,
    _token_coverage,
    _tokenize,
)
from adsp.core.memory import ConversationMemory
from adsp.core.orchestrator import _merge_retrieved_contexts
from adsp.core.types import Citation, RetrievedContext


def test_filter_history_follow_up_returns_recent_items():
    history = [
        {"query": "where is it located", "response": "near the river"},
        {"query": "what is the price", "response": "low"},
        {"query": "is it available", "response": "yes"},
    ]
    context_filter = ConversationContextFilter(backend="heuristic", enabled=True)
    filtered = context_filter.filter_history(history, query="what about price?")
    assert len(filtered) == 2
    assert filtered[0]["query"] == "what is the price"
    assert filtered[1]["query"] == "is it available"


def test_filter_history_by_token_coverage():
    history = [
        {"query": "where is it located", "response": "near the river"},
        {"query": "what is the price", "response": "low and stable"},
        {"query": "how is the service", "response": "friendly"},
    ]
    context_filter = ConversationContextFilter(
        backend="heuristic",
        enabled=True,
        max_history_items=2,
        min_coverage=0.2,
    )
    filtered = context_filter.filter_history(history, query="price range")
    assert len(filtered) == 1
    assert "price" in filtered[0]["query"]


def test_filter_retrieved_context_blocks():
    blocks = [
        "Persona: X | Indicator: Price\nPrice range is low.",
        "Persona: X | Indicator: Location\nLocated near the river.",
        "Persona: X | Indicator: Service\nService is friendly.",
    ]
    separator = "\n\n---\n\n"
    retrieved = RetrievedContext(
        context=separator.join(blocks),
        citations=[Citation(indicator_id="price"), Citation(indicator_id="location"), Citation(indicator_id="service")],
        raw={"documents": [{"id": "price"}, {"id": "location"}, {"id": "service"}]},
    )
    context_filter = ConversationContextFilter(
        backend="heuristic",
        enabled=True,
        max_context_blocks=2,
        min_coverage=0.2,
    )
    filtered = context_filter.filter_retrieved(retrieved, query="price details")
    assert "Price range is low." in filtered.context
    assert "Located near the river." not in filtered.context
    assert len(filtered.citations) == 1
    assert filtered.citations[0].indicator_id == "price"
    assert filtered.raw.get("context_keep") == [0]
    assert filtered.raw.get("documents") == [{"id": "price"}]


def test_tokenize_splits_words():
    assert _tokenize("Hello-world") == ["hello-world"]
    assert _tokenize("A_B") == ["a_b"]


def test_meaningful_tokens_removes_stopwords():
    tokens = _meaningful_tokens("this is a test")
    assert tokens == ["test"]


def test_token_coverage_basic():
    coverage = _token_coverage(["price", "range"], "price is low")
    assert coverage == 0.5


def test_token_coverage_no_tokens():
    assert _token_coverage([], "text") == 0.0


def test_looks_like_follow_up_prefix():
    assert _looks_like_follow_up("and what about price") is True


def test_looks_like_follow_up_pronoun():
    assert _looks_like_follow_up("is it available") is True


def test_looks_like_follow_up_long_query():
    assert _looks_like_follow_up("what is the price range") is False


def test_split_context_blocks_handles_separator():
    context = "A\n\n---\n\nB"
    blocks = _split_context_blocks(context)
    assert blocks == ["A", "B"]


def test_join_context_blocks_round_trip():
    blocks = ["A", "B"]
    joined = _join_context_blocks(blocks)
    assert "A" in joined
    assert "B" in joined


def test_extract_json_from_fenced_block():
    payload = """
```json
{"keep_history": [1]}
```
"""
    assert _extract_json(payload) == "{\"keep_history\": [1]}"


def test_extract_json_from_inline_block():
    payload = "{\"keep_context\": [0]}"
    assert _extract_json(payload) == payload


def test_memory_store_and_trim():
    memory = ConversationMemory(max_items=2)
    memory.store("p1", {"query": "q1", "response": "a1"}, session_id="s1")
    memory.store("p1", {"query": "q2", "response": "a2"}, session_id="s1")
    memory.store("p1", {"query": "q3", "response": "a3"}, session_id="s1")
    history = memory.get_history("p1", session_id="s1")
    assert len(history) == 2
    assert history[0]["query"] == "q2"
    assert history[1]["query"] == "q3"


def test_memory_separates_sessions():
    memory = ConversationMemory()
    memory.store("p1", {"query": "q1", "response": "a1"})
    memory.store("p1", {"query": "q2", "response": "a2"}, session_id="s1")
    default_history = memory.get_history("p1")
    session_history = memory.get_history("p1", session_id="s1")
    assert len(default_history) == 1
    assert len(session_history) == 1


def test_merge_retrieved_contexts_combines_blocks():
    primary = RetrievedContext(
        context="A",
        citations=[Citation(indicator_id="a")],
        raw={"documents": [{"id": "a"}]},
    )
    secondary = RetrievedContext(
        context="B",
        citations=[Citation(indicator_id="b")],
        raw={"documents": [{"id": "b"}]},
    )
    merged = _merge_retrieved_contexts(primary, secondary)
    assert "A" in merged.context
    assert "B" in merged.context
    assert len(merged.citations) == 2
    assert merged.raw["documents"][0]["id"] == "a"
    assert merged.raw["documents"][1]["id"] == "b"


def test_merge_retrieved_contexts_handles_missing_docs():
    primary = RetrievedContext(context="A", citations=[], raw={})
    secondary = RetrievedContext(context="B", citations=[], raw={"documents": []})
    merged = _merge_retrieved_contexts(primary, secondary)
    assert merged.raw["documents"] == []
