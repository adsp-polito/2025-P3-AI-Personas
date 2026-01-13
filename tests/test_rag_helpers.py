"""RAG helper and embedding tests."""

from pathlib import Path

import pytest

pytest.importorskip('langchain_core')

from langchain_core.documents import Document

from adsp.core.rag.fact_data_index import _safe_dir_has_files
from adsp.core.rag.fact_data_index import build_fact_data_index_from_markdown
from adsp.core.rag.persona_index import HashEmbeddings
from adsp.data_pipeline.fact_data_pipeline.rag.indicator import (
    documents_to_context_prompt as fact_prompt,
)
from adsp.data_pipeline.persona_data_pipeline.rag.indicator import PersonaIndicatorRAG
from adsp.data_pipeline.persona_data_pipeline.rag.indicator import (
    documents_to_context_prompt as persona_prompt,
)
from adsp.data_pipeline.schema import Indicator, Metric, PersonaProfileModel, Source, Statement


def build_persona() -> PersonaProfileModel:
    return PersonaProfileModel(persona_id='p1', persona_name='Alpha')


def build_indicator() -> Indicator:
    return Indicator(
        id='i1',
        label='Price',
        domain='Value',
        category='Cost',
        description='Low',
        sources=[Source(doc_id='doc1', pages=[1])],
        statements=[
            Statement(
                label='Budget',
                description='Affordable',
                metrics=[Metric(value=10, unit='$', description='avg')],
            )
        ],
    )


def test_hash_embeddings_dimension():
    emb = HashEmbeddings(dim=8)
    vec = emb.embed_query('hello')

    assert len(vec) == 8
    assert all(isinstance(item, float) for item in vec)


def test_hash_embeddings_empty_text_returns_zero_vector():
    emb = HashEmbeddings(dim=6)
    vec = emb.embed_query('')

    assert vec == [0.0] * 6
    assert len(vec) == 6


def test_hash_embeddings_raises_on_invalid_dim():
    with pytest.raises(ValueError):
        HashEmbeddings(dim=0)


def test_hash_embeddings_repeatable_length():
    emb = HashEmbeddings(dim=4)
    vec_one = emb.embed_query('alpha')
    vec_two = emb.embed_query('alpha')

    assert len(vec_one) == 4
    assert len(vec_two) == 4


def test_persona_indicator_rag_render_indicator():
    persona = build_persona()
    indicator = build_indicator()

    rag = PersonaIndicatorRAG(HashEmbeddings())
    rendered = rag._render_indicator(persona, indicator)

    assert 'Persona: Alpha' in rendered
    assert 'Indicator: Price' in rendered
    assert 'Statements:' in rendered


def test_persona_prompt_headers():
    doc = Document(
        page_content='Content',
        metadata={
            'persona_name': 'Alpha',
            'indicator_label': 'Price',
            'domain': 'Value',
            'category': 'Cost',
            'sources': [{'doc_id': 'doc1', 'pages': [1, 2]}],
        },
    )

    prompt = persona_prompt([doc])

    assert 'Persona: Alpha' in prompt
    assert 'Indicator: Price' in prompt
    assert 'Domain: Value' in prompt
    assert 'Category: Cost' in prompt


def test_persona_prompt_includes_sources():
    doc = Document(
        page_content='Content',
        metadata={
            'persona_name': 'Alpha',
            'indicator_label': 'Taste',
            'domain': 'Quality',
            'category': 'Flavor',
            'sources': [{'doc_id': 'doc2', 'pages': [3]}],
        },
    )

    prompt = persona_prompt([doc])

    assert 'Source:' in prompt
    assert 'doc2' in prompt


def test_fact_prompt_headers():
    doc = Document(
        page_content='Content',
        metadata={
            'segment': 'Segment A',
            'section': 'Section 1',
            'template': 'Template X',
            'page_number': 3,
            'source_file': 'page_0003.md',
        },
    )

    prompt = fact_prompt([doc])

    assert 'Segment: Segment A' in prompt
    assert 'Section: Section 1' in prompt
    assert 'Template: Template X' in prompt
    assert 'Page: 3' in prompt
    assert 'Source: page_0003.md' in prompt


def test_safe_dir_has_files_false_for_missing(tmp_path: Path):
    missing = tmp_path / 'missing'
    assert _safe_dir_has_files(missing, pattern='*.md') is False


def test_safe_dir_has_files_true_with_file(tmp_path: Path):
    path = tmp_path / 'page_1.md'
    path.write_text('content', encoding='utf-8')

    assert _safe_dir_has_files(tmp_path, pattern='*.md') is True


def test_safe_dir_has_files_respects_pattern(tmp_path: Path):
    (tmp_path / 'page_1.md').write_text('content', encoding='utf-8')
    (tmp_path / 'note.txt').write_text('note', encoding='utf-8')

    assert _safe_dir_has_files(tmp_path, pattern='*.txt') is True
    assert _safe_dir_has_files(tmp_path, pattern='*.csv') is False


def test_build_fact_data_index_from_markdown_no_files(tmp_path: Path):
    index = build_fact_data_index_from_markdown(tmp_path, pattern='*.md')
    assert index is None
