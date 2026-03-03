"""Shared utilities for working with embedding models."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import TYPE_CHECKING
import weakref

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings


DEFAULT_EMBEDDING_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
EMBEDDING_MODEL_ENV_VAR = "ADSP_EMBEDDING_MODEL_NAME"
EMBEDDING_DEVICE_ENV_VAR = "ADSP_EMBEDDING_DEVICE"
EMBEDDING_BATCH_SIZE_ENV_VAR = "ADSP_EMBEDDING_BATCH_SIZE"
AUTO_EMBEDDING_DEVICE = "auto"


def get_configured_embedding_model_name() -> str:
    """Return the configured embedding model name from env or the repo default."""

    raw = os.environ.get(EMBEDDING_MODEL_ENV_VAR, "").strip()
    return raw or DEFAULT_EMBEDDING_MODEL_NAME


@dataclass(frozen=True)
class EmbeddingModelConfig:
    model_name: str
    device: str | None
    batch_size: int | None


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
        model_name=model_name or get_configured_embedding_model_name(),
        device=device,
        batch_size=batch_size,
    )


def build_configured_embeddings(*, model_name: str | None = None) -> "Embeddings":
    """Create HuggingFace embeddings with env-configured runtime options."""

    from langchain_huggingface import HuggingFaceEmbeddings

    config = get_configured_embedding_config(model_name=model_name)
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
    "DEFAULT_EMBEDDING_MODEL_NAME",
    "EMBEDDING_MODEL_ENV_VAR",
    "EMBEDDING_DEVICE_ENV_VAR",
    "EMBEDDING_BATCH_SIZE_ENV_VAR",
    "AUTO_EMBEDDING_DEVICE",
    "EmbeddingModelConfig",
    "build_configured_embeddings",
    "get_available_embedding_device",
    "get_configured_embedding_config",
    "get_configured_embedding_model_name",
    "get_embedding_dimension",
]
