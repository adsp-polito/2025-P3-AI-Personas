"""RAG helper and embedding tests."""

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip('langchain_core')

from langchain_core.documents import Document

from adsp.core.rag.fact_data_index import _safe_dir_has_files, build_fact_data_index_from_markdown
from adsp.core.rag.persona_index import HashEmbeddings
from adsp.data_pipeline.embedding_utils import (
    OpenAICompatibleEmbeddings,
    build_configured_embeddings,
    get_configured_embedding_config,
    get_configured_embedding_signature,
)
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
    monkeypatch.delenv("ADSP_EMBEDDING_BACKEND", raising=False)
    monkeypatch.delenv("ADSP_EMBEDDING_DEVICE", raising=False)
    monkeypatch.delenv("ADSP_EMBEDDING_BATCH_SIZE", raising=False)
    monkeypatch.setattr(
        "adsp.data_pipeline.embedding_utils.get_available_embedding_device",
        lambda: "cuda",
    )
    config = get_configured_embedding_config(model_name="test-model")
    assert config.backend == "huggingface"
    assert config.model_name == "test-model"
    assert config.device == "cuda"
    assert config.batch_size is None


def test_embedding_config_reads_device_and_batch_size(monkeypatch):
    monkeypatch.delenv("ADSP_EMBEDDING_BACKEND", raising=False)
    monkeypatch.setenv("ADSP_EMBEDDING_DEVICE", "cuda")
    monkeypatch.setenv("ADSP_EMBEDDING_BATCH_SIZE", "64")
    config = get_configured_embedding_config(model_name="test-model")
    assert config.device == "cuda"
    assert config.batch_size == 64


def test_embedding_config_auto_device_uses_available_device(monkeypatch):
    monkeypatch.delenv("ADSP_EMBEDDING_BACKEND", raising=False)
    monkeypatch.setenv("ADSP_EMBEDDING_DEVICE", "auto")
    monkeypatch.setattr(
        "adsp.data_pipeline.embedding_utils.get_available_embedding_device",
        lambda: "mps",
    )
    config = get_configured_embedding_config(model_name="test-model")
    assert config.device == "mps"


def test_embedding_config_openai_backend_reads_extra_body(monkeypatch):
    monkeypatch.setenv("ADSP_EMBEDDING_BACKEND", "openai")
    monkeypatch.setenv("ADSP_EMBEDDING_API_BASE_URL", "https://integrate.api.nvidia.com/v1")
    monkeypatch.setenv("ADSP_EMBEDDING_QUERY_EXTRA_BODY", '{"input_type":"query"}')
    monkeypatch.setenv("ADSP_EMBEDDING_DOCUMENT_EXTRA_BODY", '{"input_type":"passage"}')

    config = get_configured_embedding_config(model_name="nvidia/embed")

    assert config.backend == "openai"
    assert config.model_name == "nvidia/embed"
    assert config.device is None
    assert config.batch_size is None
    assert config.api_base_url == "https://integrate.api.nvidia.com/v1"
    assert config.query_extra_body == {"input_type": "query"}
    assert config.document_extra_body == {"input_type": "passage"}


def test_embedding_signature_changes_with_backend(monkeypatch):
    monkeypatch.setenv("ADSP_EMBEDDING_BACKEND", "huggingface")
    signature_one = get_configured_embedding_signature(model_name="model-a")

    monkeypatch.setenv("ADSP_EMBEDDING_BACKEND", "openai")
    monkeypatch.setenv("ADSP_EMBEDDING_API_BASE_URL", "https://integrate.api.nvidia.com/v1")
    signature_two = get_configured_embedding_signature(model_name="model-a")

    assert signature_one != signature_two


class _FakeEmbeddingsEndpoint:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        items = []
        for index, text in enumerate(kwargs["input"]):
            items.append(SimpleNamespace(index=index, embedding=[float(len(text)), float(index)]))
        return SimpleNamespace(data=items)


class _FakeOpenAIClient:
    def __init__(self, *, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.embeddings = _FakeEmbeddingsEndpoint()


def test_build_configured_embeddings_openai_backend(monkeypatch):
    fake_client_holder = {}

    def _factory(*, api_key: str, base_url: str):
        client = _FakeOpenAIClient(api_key=api_key, base_url=base_url)
        fake_client_holder["client"] = client
        return client

    monkeypatch.setenv("ADSP_EMBEDDING_BACKEND", "openai")
    monkeypatch.setenv("ADSP_EMBEDDING_MODEL_NAME", "nvidia/embed")
    monkeypatch.setenv("ADSP_EMBEDDING_API_BASE_URL", "https://integrate.api.nvidia.com/v1")
    monkeypatch.setenv("ADSP_EMBEDDING_API_KEY", "secret")
    monkeypatch.setenv("ADSP_EMBEDDING_ENCODING_FORMAT", "float")
    monkeypatch.setenv(
        "ADSP_EMBEDDING_QUERY_EXTRA_BODY",
        '{"modality":["text"],"input_type":"query","truncate":"NONE"}',
    )
    monkeypatch.setenv(
        "ADSP_EMBEDDING_DOCUMENT_EXTRA_BODY",
        '{"modality":["text"],"input_type":"passage","truncate":"NONE"}',
    )
    monkeypatch.setattr("openai.OpenAI", _factory)

    embeddings = build_configured_embeddings()

    assert isinstance(embeddings, OpenAICompatibleEmbeddings)
    assert embeddings.embed_query("hello") == [5.0, 0.0]
    assert embeddings.embed_documents(["abc", "de"]) == [[3.0, 0.0], [2.0, 1.0]]

    calls = fake_client_holder["client"].embeddings.calls
    assert calls[0]["model"] == "nvidia/embed"
    assert calls[0]["encoding_format"] == "float"
    assert calls[0]["extra_body"]["input_type"] == "query"
    assert calls[1]["extra_body"]["input_type"] == "passage"


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


def test_vectorstore_provider_uses_writable_fallback_when_primary_is_read_only(tmp_path: Path):
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

    primary = provider._faiss_dir("fact-data")
    primary.mkdir(parents=True, exist_ok=True)
    primary.chmod(0o555)

    try:
        provider.persist("fact-data", fingerprint="fingerprint-1", vectorstore=store)
        assert provider._faiss_read_dirs("fact-data")[0] == provider._faiss_fallback_dir("fact-data")
    finally:
        primary.chmod(0o755)

    assert store.saved_paths
    assert Path(store.saved_paths[-1]) == provider._faiss_fallback_dir("fact-data")
    assert (provider._faiss_fallback_dir("fact-data") / "index.faiss").exists()
    assert provider._manifest_path("fact-data").exists()
    assert str(provider._faiss_fallback_dir("fact-data")).endswith(f"uid-{os.getuid()}/adsp-fact-data")


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
