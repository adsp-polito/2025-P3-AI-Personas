"""
Tests for RAG helpers and embeddings.
"""

import pytest

pytest.importorskip("langchain_core")

from pathlib import Path

from langchain_core.documents import Document

from adsp.core.rag.fact_data_index import _safe_dir_has_files, build_fact_data_index_from_markdown
from adsp.core.rag.persona_index import HashEmbeddings
from adsp.data_pipeline.fact_data_pipeline.rag.indicator import documents_to_context_prompt as fact_prompt
from adsp.data_pipeline.persona_data_pipeline.rag.indicator import (
    PersonaIndicatorRAG,
    documents_to_context_prompt as persona_prompt,
)
from adsp.data_pipeline.schema import Indicator, Metric, PersonaProfileModel, Source, Statement


def test_hash_embeddings_dimension():
    emb = HashEmbeddings(dim=8)
    vec = emb.embed_query("hello")
    assert len(vec) == 8


def test_hash_embeddings_empty_text_returns_zero_vector():
    emb = HashEmbeddings(dim=6)
    vec = emb.embed_query("")
    assert vec == [0.0] * 6


def test_hash_embeddings_raises_on_invalid_dim():
    with pytest.raises(ValueError):
        HashEmbeddings(dim=0)


def test_persona_indicator_rag_render_indicator():
    persona = PersonaProfileModel(persona_id="p1", persona_name="Alpha")
    indicator = Indicator(
        id="i1",
        label="Price",
        domain="Value",
        category="Cost",
        description="Low",
        sources=[Source(doc_id="doc1", pages=[1])],
        statements=[
            Statement(
                label="Budget",
                description="Affordable",
                metrics=[Metric(value=10, unit="$", description="avg")],
            )
        ],
    )
    rag = PersonaIndicatorRAG(HashEmbeddings())
    rendered = rag._render_indicator(persona, indicator)
    assert "Persona: Alpha" in rendered
    assert "Indicator: Price" in rendered
    assert "Statements:" in rendered


def test_persona_documents_to_context_prompt_headers():
    doc = Document(
        page_content="Content",
        metadata={
            "persona_name": "Alpha",
            "indicator_label": "Price",
            "domain": "Value",
            "category": "Cost",
            "sources": [{"doc_id": "doc1", "pages": [1, 2]}],
        },
    )
    prompt = persona_prompt([doc])
    assert "Persona: Alpha" in prompt
    assert "Indicator: Price" in prompt
    assert "Domain: Value" in prompt
    assert "Category: Cost" in prompt


def test_fact_documents_to_context_prompt_headers():
    doc = Document(
        page_content="Content",
        metadata={
            "segment": "Segment A",
            "section": "Section 1",
            "template": "Template X",
            "page_number": 3,
            "source_file": "page_0003.md",
        },
    )
    prompt = fact_prompt([doc])
    assert "Segment: Segment A" in prompt
    assert "Section: Section 1" in prompt
    assert "Template: Template X" in prompt
    assert "Page: 3" in prompt
    assert "Source: page_0003.md" in prompt


def test_safe_dir_has_files_false_for_missing(tmp_path: Path):
    missing = tmp_path / "missing"
    assert _safe_dir_has_files(missing, pattern="*.md") is False


def test_safe_dir_has_files_true_with_file(tmp_path: Path):
    path = tmp_path / "page_1.md"
    path.write_text("content", encoding="utf-8")
    assert _safe_dir_has_files(tmp_path, pattern="*.md") is True


def test_build_fact_data_index_from_markdown_no_files(tmp_path: Path):
    index = build_fact_data_index_from_markdown(tmp_path, pattern="*.md")
    assert index is None
