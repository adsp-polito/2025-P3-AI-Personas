"""Shared utilities for working with embedding models."""

from __future__ import annotations

from typing import TYPE_CHECKING
import weakref

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings

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
