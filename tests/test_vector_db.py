"""
Tests for vector database storage.

Simple checks for document insertion and retrieval.
"""

from adsp.storage.vector_db import VectorDatabase


def test_upsert_document():
    db = VectorDatabase()
    db.upsert("persona1", "test document")

    result = db.search("persona1", "query")
    assert result == "test document"


def test_search_empty_persona():
    db = VectorDatabase()
    result = db.search("unknown", "query")
    assert result == ""


def test_multiple_documents():
    db = VectorDatabase()
    db.upsert("p1", "doc1")
    db.upsert("p1", "doc2")
    db.upsert("p1", "doc3")

    # returns last document
    result = db.search("p1", "anything")
    assert result == "doc3"


def test_separate_personas():
    db = VectorDatabase()
    db.upsert("persona_a", "content_a")
    db.upsert("persona_b", "content_b")

    assert db.search("persona_a", "q") == "content_a"
    assert db.search("persona_b", "q") == "content_b"
