"""RAG helper and embedding tests."""

from pathlib import Path

import pytest

pytest.importorskip('langchain_core')

from langchain_core.documents import Document

from adsp.core.rag.fact_data_index import _safe_dir_has_files, build_fact_data_index_from_markdown
from adsp.core.rag.persona_index import HashEmbeddings
from adsp.data_pipeline.embedding_utils import get_configured_embedding_config
from adsp.data_pipeline.fact_data_pipeline.rag.indicator import (
    documents_to_context_prompt as fact_prompt,
)
from adsp.data_pipeline.persona_data_pipeline.rag.indicator import PersonaIndicatorRAG
from adsp.data_pipeline.persona_data_pipeline.rag.indicator import (
    documents_to_context_prompt as persona_prompt,
)
from adsp.data_pipeline.schema import Indicator, Metric, PersonaProfileModel, Source, Statement
from adsp.storage.langchain_vectorstore import (
    DEFAULT_VECTORSTORE_BACKEND,
    VectorStoreConfig,
    VectorStoreProvider,
    build_collection_name,
    get_vectorstore_config,
)


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


def test_safe_dir_has_files_finds_nested_markdown(tmp_path: Path):
    nested = tmp_path / 'nested'
    nested.mkdir()
    (nested / 'page_1.md').write_text('content', encoding='utf-8')

    assert _safe_dir_has_files(tmp_path, pattern='*.md') is True


def test_build_fact_data_index_from_markdown_no_files(tmp_path: Path):
    index = build_fact_data_index_from_markdown(tmp_path, pattern='*.md')
    assert index is None


def test_embedding_config_defaults(monkeypatch):
    monkeypatch.delenv("ADSP_EMBEDDING_DEVICE", raising=False)
    monkeypatch.delenv("ADSP_EMBEDDING_BATCH_SIZE", raising=False)
    monkeypatch.setattr(
        "adsp.data_pipeline.embedding_utils.get_available_embedding_device",
        lambda: "cuda",
    )
    config = get_configured_embedding_config(model_name="test-model")
    assert config.model_name == "test-model"
    assert config.device == "cuda"
    assert config.batch_size is None


def test_embedding_config_reads_device_and_batch_size(monkeypatch):
    monkeypatch.setenv("ADSP_EMBEDDING_DEVICE", "cuda")
    monkeypatch.setenv("ADSP_EMBEDDING_BATCH_SIZE", "64")
    config = get_configured_embedding_config(model_name="test-model")
    assert config.device == "cuda"
    assert config.batch_size == 64


def test_embedding_config_auto_device_uses_available_device(monkeypatch):
    monkeypatch.setenv("ADSP_EMBEDDING_DEVICE", "auto")
    monkeypatch.setattr(
        "adsp.data_pipeline.embedding_utils.get_available_embedding_device",
        lambda: "mps",
    )
    config = get_configured_embedding_config(model_name="test-model")
    assert config.device == "mps"


def test_vectorstore_config_defaults(monkeypatch):
    monkeypatch.delenv("ADSP_VECTORSTORE_BACKEND", raising=False)
    config = get_vectorstore_config()
    assert config.backend == DEFAULT_VECTORSTORE_BACKEND


def test_vectorstore_config_rejects_invalid_backend(monkeypatch):
    monkeypatch.setenv("ADSP_VECTORSTORE_BACKEND", "unknown")
    with pytest.raises(ValueError):
        get_vectorstore_config()


def test_build_collection_name_sanitizes_namespace(monkeypatch):
    monkeypatch.setenv("ADSP_VECTORSTORE_COLLECTION_PREFIX", "My App")
    monkeypatch.setenv("ADSP_VECTORSTORE_BACKEND", "faiss")
    name = build_collection_name(namespace="Persona / Alpha")
    assert name == "my-app-persona-alpha"


def test_vectorstore_provider_caches_namespaces():
    emb = HashEmbeddings()
    provider = VectorStoreProvider(embeddings=emb)

    store_one = provider.get("persona-alpha")
    store_two = provider.get("persona-alpha")
    store_three = provider.get("fact-data")

    assert store_one is store_two
    assert store_one is not store_three


class _FakePersistedStore:
    def __init__(self):
        self.saved_paths = []

    def save_local(self, path: str) -> None:
        path_obj = Path(path)
        path_obj.mkdir(parents=True, exist_ok=True)
        (path_obj / "index.faiss").write_text("stub", encoding="utf-8")
        self.saved_paths.append(path)


def test_vectorstore_provider_loads_persisted_store_when_fingerprint_matches(tmp_path: Path, monkeypatch):
    emb = HashEmbeddings()
    provider = VectorStoreProvider(
        embeddings=emb,
        config=VectorStoreConfig(
            backend="faiss",
            persist_dir=tmp_path,
            collection_prefix="adsp",
        ),
    )
    store = _FakePersistedStore()
    loaded_store = object()

    monkeypatch.setattr(provider, "_load_persisted", lambda namespace: loaded_store)

    provider.persist("persona-alpha", fingerprint="fingerprint-1", vectorstore=store)

    assert provider.load("persona-alpha", fingerprint="fingerprint-1") is loaded_store


def test_vectorstore_provider_skips_persisted_store_when_fingerprint_changes(tmp_path: Path, monkeypatch):
    emb = HashEmbeddings()
    provider = VectorStoreProvider(
        embeddings=emb,
        config=VectorStoreConfig(
            backend="faiss",
            persist_dir=tmp_path,
            collection_prefix="adsp",
        ),
    )
    store = _FakePersistedStore()
    load_calls = []

    def _fake_load(namespace: str):
        load_calls.append(namespace)
        return object()

    monkeypatch.setattr(provider, "_load_persisted", _fake_load)

    provider.persist("persona-alpha", fingerprint="fingerprint-1", vectorstore=store)

    assert provider.load("persona-alpha", fingerprint="fingerprint-2") is None
    assert load_calls == []
