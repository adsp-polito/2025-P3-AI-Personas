"""Shared utilities for working with embedding models."""

from __future__ import annotations

from typing import TYPE_CHECKING
import weakref

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings

# Cache for embedding dimensions, using weak references to avoid memory leaks
_dimension_cache: weakref.WeakKeyDictionary[Embeddings, int] = weakref.WeakKeyDictionary()


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
    if embeddings in _dimension_cache:
        return _dimension_cache[embeddings]
    
    # Compute dimension by embedding a probe string
    probe_vector = embeddings.embed_query("dimension probe")
    dimension = len(probe_vector)
    
    # Cache the result
    _dimension_cache[embeddings] = dimension
    
    return dimension
