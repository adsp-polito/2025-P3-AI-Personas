"""Shared RAG utilities for embedding and vector store operations."""

from __future__ import annotations

from langchain_core.embeddings import Embeddings


def get_embedding_dimension(embeddings: Embeddings) -> int:
    """Get the dimension of the embedding model efficiently.
    
    Tries multiple methods in order of efficiency:
    1. Check for a 'dim' attribute (e.g., HashEmbeddings)
    2. Check for a 'dimension' attribute
    3. Check for the underlying model's get_sentence_embedding_dimension() method
    4. Fall back to probing with a test query (least efficient)
    
    Args:
        embeddings: The embeddings model to get the dimension from.
    
    Returns:
        The dimension of the embedding vectors produced by the model.
    """
    # Try direct dim attribute
    if hasattr(embeddings, 'dim'):
        return embeddings.dim
    
    # Try dimension attribute
    if hasattr(embeddings, 'dimension'):
        return embeddings.dimension
    
    # Try SentenceTransformer's method via the model attribute
    if hasattr(embeddings, 'model') and hasattr(embeddings.model, 'get_sentence_embedding_dimension'):
        return embeddings.model.get_sentence_embedding_dimension()
    
    # Try accessing client attribute for certain embedding types
    if hasattr(embeddings, 'client') and hasattr(embeddings.client, 'get_sentence_embedding_dimension'):
        return embeddings.client.get_sentence_embedding_dimension()
    
    # Fall back to probing (least efficient, but works for any Embeddings implementation)
    return len(embeddings.embed_query("dimension probe"))


__all__ = ["get_embedding_dimension"]
