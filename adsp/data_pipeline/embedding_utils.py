"""Shared utilities for working with embedding models."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any
import weakref

from langchain_core.embeddings import Embeddings


DEFAULT_EMBEDDING_BACKEND = "huggingface"
DEFAULT_EMBEDDING_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
EMBEDDING_BACKEND_ENV_VAR = "ADSP_EMBEDDING_BACKEND"
EMBEDDING_MODEL_ENV_VAR = "ADSP_EMBEDDING_MODEL_NAME"
EMBEDDING_DEVICE_ENV_VAR = "ADSP_EMBEDDING_DEVICE"
EMBEDDING_BATCH_SIZE_ENV_VAR = "ADSP_EMBEDDING_BATCH_SIZE"
EMBEDDING_API_BASE_URL_ENV_VAR = "ADSP_EMBEDDING_API_BASE_URL"
EMBEDDING_API_KEY_ENV_VAR = "ADSP_EMBEDDING_API_KEY"
EMBEDDING_ENCODING_FORMAT_ENV_VAR = "ADSP_EMBEDDING_ENCODING_FORMAT"
EMBEDDING_EXTRA_BODY_ENV_VAR = "ADSP_EMBEDDING_EXTRA_BODY"
EMBEDDING_QUERY_EXTRA_BODY_ENV_VAR = "ADSP_EMBEDDING_QUERY_EXTRA_BODY"
EMBEDDING_DOCUMENT_EXTRA_BODY_ENV_VAR = "ADSP_EMBEDDING_DOCUMENT_EXTRA_BODY"
AUTO_EMBEDDING_DEVICE = "auto"
OPENAI_COMPATIBLE_EMBEDDING_BACKENDS = {"openai", "openai-compatible", "openai_compatible"}


def get_configured_embedding_backend() -> str:
    """Return the configured embedding backend from env or the repo default."""

    raw = os.environ.get(EMBEDDING_BACKEND_ENV_VAR, "").strip().lower()
    if raw in OPENAI_COMPATIBLE_EMBEDDING_BACKENDS:
        return "openai"
    return raw or DEFAULT_EMBEDDING_BACKEND


def get_configured_embedding_model_name() -> str:
    """Return the configured embedding model name from env or the repo default."""

    raw = os.environ.get(EMBEDDING_MODEL_ENV_VAR, "").strip()
    return raw or DEFAULT_EMBEDDING_MODEL_NAME


def _parse_json_object_env(name: str) -> dict[str, Any] | None:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} must be valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{name} must be a JSON object.")
    return parsed


def _get_configured_embedding_api_base_url() -> str | None:
    for env_var in (EMBEDDING_API_BASE_URL_ENV_VAR, "ADSP_LLM_BASE_URL", "VLLM_BASE_URL"):
        raw = os.environ.get(env_var, "").strip()
        if raw:
            return raw
    return None


def _get_configured_embedding_api_key() -> str | None:
    for env_var in (
        EMBEDDING_API_KEY_ENV_VAR,
        "NVIDIA_API_KEY",
        "OPENAI_API_KEY",
        "ADSP_LLM_API_KEY",
        "VLLM_API_KEY",
    ):
        raw = os.environ.get(env_var, "").strip()
        if raw:
            return raw
    return None


@dataclass(frozen=True)
class EmbeddingModelConfig:
    backend: str
    model_name: str
    device: str | None
    batch_size: int | None
    api_base_url: str | None = None
    encoding_format: str | None = None
    extra_body: dict[str, Any] | None = None
    query_extra_body: dict[str, Any] | None = None
    document_extra_body: dict[str, Any] | None = None

    def cache_identity(self) -> dict[str, Any]:
        """Return a stable, non-secret payload for cache fingerprinting."""

        payload: dict[str, Any] = {
            "backend": self.backend,
            "model_name": self.model_name,
        }
        if self.backend == "huggingface":
            payload["device"] = self.device
            payload["batch_size"] = self.batch_size
        elif self.backend == "openai":
            payload["api_base_url"] = self.api_base_url
            payload["encoding_format"] = self.encoding_format
            payload["extra_body"] = self.extra_body or {}
            payload["query_extra_body"] = self.query_extra_body or {}
            payload["document_extra_body"] = self.document_extra_body or {}
        return payload


def get_available_embedding_device() -> str:
    """Return the best available torch device for embeddings."""

    try:
        import torch
    except Exception:
        return "cpu"

    if torch.cuda.is_available():
        return "cuda"

    mps_backend = getattr(torch.backends, "mps", None)
    if mps_backend is not None and mps_backend.is_available():
        return "mps"

    return "cpu"


def get_configured_embedding_config(*, model_name: str | None = None) -> EmbeddingModelConfig:
    """Return embedding runtime settings from env."""

    backend = get_configured_embedding_backend()
    resolved_model_name = model_name or get_configured_embedding_model_name()

    if backend == "openai":
        encoding_format_raw = os.environ.get(EMBEDDING_ENCODING_FORMAT_ENV_VAR, "").strip()
        return EmbeddingModelConfig(
            backend=backend,
            model_name=resolved_model_name,
            device=None,
            batch_size=None,
            api_base_url=_get_configured_embedding_api_base_url(),
            encoding_format=encoding_format_raw or "float",
            extra_body=_parse_json_object_env(EMBEDDING_EXTRA_BODY_ENV_VAR),
            query_extra_body=_parse_json_object_env(EMBEDDING_QUERY_EXTRA_BODY_ENV_VAR),
            document_extra_body=_parse_json_object_env(EMBEDDING_DOCUMENT_EXTRA_BODY_ENV_VAR),
        )

    if backend != "huggingface":
        raise ValueError(
            f"Unsupported {EMBEDDING_BACKEND_ENV_VAR}={backend!r}. "
            "Supported values: huggingface, openai."
        )

    device_raw = os.environ.get(EMBEDDING_DEVICE_ENV_VAR, "").strip()
    batch_size_raw = os.environ.get(EMBEDDING_BATCH_SIZE_ENV_VAR, "").strip()
    device = device_raw or AUTO_EMBEDDING_DEVICE
    if device.lower() == AUTO_EMBEDDING_DEVICE:
        device = get_available_embedding_device()

    batch_size: int | None = None
    if batch_size_raw:
        try:
            parsed = int(batch_size_raw)
            if parsed > 0:
                batch_size = parsed
        except Exception:
            batch_size = None

    return EmbeddingModelConfig(
        backend=backend,
        model_name=resolved_model_name,
        device=device,
        batch_size=batch_size,
    )


def get_configured_embedding_signature(*, model_name: str | None = None) -> str:
    """Return a stable signature for the configured embedding backend."""

    config = get_configured_embedding_config(model_name=model_name)
    return json.dumps(config.cache_identity(), sort_keys=True, separators=(",", ":"))


class OpenAICompatibleEmbeddings(Embeddings):
    """Embeddings adapter for OpenAI-compatible APIs such as NVIDIA NIM."""

    def __init__(
        self,
        *,
        model_name: str,
        api_key: str,
        api_base_url: str,
        encoding_format: str | None = None,
        extra_body: dict[str, Any] | None = None,
        query_extra_body: dict[str, Any] | None = None,
        document_extra_body: dict[str, Any] | None = None,
    ) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "openai is required for ADSP_EMBEDDING_BACKEND=openai. "
                "Install deps with `pip install openai`."
            ) from exc

        self.model_name = model_name
        self.api_base_url = api_base_url
        self.encoding_format = encoding_format
        self._client = OpenAI(api_key=api_key, base_url=api_base_url)
        self._extra_body = dict(extra_body or {})
        self._query_extra_body = dict(query_extra_body or {})
        self._document_extra_body = dict(document_extra_body or {})

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._embed(texts, extra_body=self._document_extra_body)

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text], extra_body=self._query_extra_body)[0]

    def _embed(self, texts: list[str], *, extra_body: dict[str, Any]) -> list[list[float]]:
        kwargs: dict[str, Any] = {
            "input": texts,
            "model": self.model_name,
        }
        if self.encoding_format:
            kwargs["encoding_format"] = self.encoding_format

        merged_extra_body = dict(self._extra_body)
        merged_extra_body.update(extra_body)
        if merged_extra_body:
            kwargs["extra_body"] = merged_extra_body

        response = self._client.embeddings.create(**kwargs)
        items = sorted(response.data, key=lambda item: getattr(item, "index", 0))
        return [list(item.embedding) for item in items]


def build_configured_embeddings(*, model_name: str | None = None) -> "Embeddings":
    """Create embeddings with env-configured backend options."""

    config = get_configured_embedding_config(model_name=model_name)

    if config.backend == "openai":
        api_base_url = config.api_base_url
        if not api_base_url:
            raise ValueError(
                "ADSP_EMBEDDING_API_BASE_URL is required when ADSP_EMBEDDING_BACKEND=openai. "
                "Fallbacks: ADSP_LLM_BASE_URL, VLLM_BASE_URL."
            )
        api_key = _get_configured_embedding_api_key()
        if not api_key:
            raise ValueError(
                "ADSP_EMBEDDING_API_KEY is required when ADSP_EMBEDDING_BACKEND=openai. "
                "Fallbacks: NVIDIA_API_KEY, OPENAI_API_KEY, ADSP_LLM_API_KEY, VLLM_API_KEY."
            )
        return OpenAICompatibleEmbeddings(
            model_name=config.model_name,
            api_key=api_key,
            api_base_url=api_base_url,
            encoding_format=config.encoding_format,
            extra_body=config.extra_body,
            query_extra_body=config.query_extra_body,
            document_extra_body=config.document_extra_body,
        )

    from langchain_huggingface import HuggingFaceEmbeddings

    model_kwargs = {}
    encode_kwargs = {}

    if config.device:
        model_kwargs["device"] = config.device
        print(f"Using device: {config.device}")
    if config.batch_size is not None:
        encode_kwargs["batch_size"] = config.batch_size

    return HuggingFaceEmbeddings(
        model_name=config.model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs,
    )

# Cache for embedding dimensions, using weak references to avoid memory leaks
_dimension_cache: weakref.WeakKeyDictionary[Embeddings, int] = weakref.WeakKeyDictionary()
_dimension_cache_by_key: dict[tuple[type, str], int] = {}


def _make_cache_key(embeddings: "Embeddings") -> tuple[type, str] | None:
    model_name = getattr(embeddings, "model_name", None)
    if model_name is None:
        model_name = getattr(embeddings, "model", None)
    if isinstance(model_name, str) and model_name:
        return (type(embeddings), model_name)
    return None


def get_embedding_dimension(embeddings: Embeddings) -> int:
    """Get the dimension of the embedding model.
    
    First checks if the embeddings object has a 'dim' attribute.
    Otherwise, computes it once by embedding a probe string and caches the result.
    
    Args:
        embeddings: The embeddings model to get the dimension for.
        
    Returns:
        The dimension of the embedding vectors.
    """
    # Check if the embeddings object exposes dimension directly
    if hasattr(embeddings, 'dim'):
        return embeddings.dim  # type: ignore[attr-defined]
    
    # Check cache first
    try:
        if embeddings in _dimension_cache:
            return _dimension_cache[embeddings]
    except TypeError:
        pass

    cache_key = _make_cache_key(embeddings)
    if cache_key is not None and cache_key in _dimension_cache_by_key:
        return _dimension_cache_by_key[cache_key]
    
    # Compute dimension by embedding a probe string
    probe_vector = embeddings.embed_query("dimension probe")
    dimension = len(probe_vector)
    
    # Cache the result
    try:
        _dimension_cache[embeddings] = dimension
    except TypeError:
        if cache_key is not None:
            _dimension_cache_by_key[cache_key] = dimension
    
    return dimension


__all__ = [
    "DEFAULT_EMBEDDING_BACKEND",
    "DEFAULT_EMBEDDING_MODEL_NAME",
    "EMBEDDING_BACKEND_ENV_VAR",
    "EMBEDDING_MODEL_ENV_VAR",
    "EMBEDDING_DEVICE_ENV_VAR",
    "EMBEDDING_BATCH_SIZE_ENV_VAR",
    "EMBEDDING_API_BASE_URL_ENV_VAR",
    "EMBEDDING_API_KEY_ENV_VAR",
    "EMBEDDING_ENCODING_FORMAT_ENV_VAR",
    "EMBEDDING_EXTRA_BODY_ENV_VAR",
    "EMBEDDING_QUERY_EXTRA_BODY_ENV_VAR",
    "EMBEDDING_DOCUMENT_EXTRA_BODY_ENV_VAR",
    "AUTO_EMBEDDING_DEVICE",
    "EmbeddingModelConfig",
    "OpenAICompatibleEmbeddings",
    "build_configured_embeddings",
    "get_available_embedding_device",
    "get_configured_embedding_backend",
    "get_configured_embedding_config",
    "get_configured_embedding_model_name",
    "get_configured_embedding_signature",
    "get_embedding_dimension",
]
