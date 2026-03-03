"""Pipeline function to chunk and index fact data markdown files."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from loguru import logger

from adsp.data_pipeline.embedding_utils import (
    build_configured_embeddings,
    get_configured_embedding_config,
    get_configured_embedding_model_name,
)
from adsp.storage.langchain_vectorstore import get_vectorstore_config
from .indicator import FactDataRAG


def run_fact_data_indexing_pipeline(
    markdown_dir: Path,
    embedding_model: Optional[Embeddings] = None,
    embedding_model_name: Optional[str] = None,
    chunk_size: int = 1200,
    chunk_overlap: int = 50,
    pattern: str = "*.md",
    vectorstore: Optional[VectorStore] = None,
) -> FactDataRAG:
    """
    Run the complete fact data indexing pipeline: chunk markdown files and index into RAG.
    
    Args:
        markdown_dir: Directory containing markdown files to index
        embedding_model: Optional pre-initialized embedding model. If None, will create from embedding_model_name
        embedding_model_name: HuggingFace model name for embeddings (default: all-mpnet-base-v2)
        chunk_size: Maximum chunk size in characters (default: 1200)
        chunk_overlap: Overlap between chunks in characters (default: 50)
        pattern: Glob pattern for markdown files (default: *.md, recursive)
        vectorstore: Optional pre-initialized vector store. If None, uses the configured backend
        
    Returns:
        FactDataRAG instance with indexed data ready for search
    """
    markdown_dir = Path(markdown_dir)
    embedding_model_name = embedding_model_name or get_configured_embedding_model_name()
    
    if not markdown_dir.exists():
        raise FileNotFoundError(f"Markdown directory not found: {markdown_dir}")
    
    logger.info("=" * 70)
    logger.info("Starting Fact Data Indexing Pipeline")
    logger.info("=" * 70)
    embedding_config = get_configured_embedding_config(model_name=embedding_model_name)
    vectorstore_config = get_vectorstore_config()
    logger.info("Indexing config: markdown_dir={}", markdown_dir)
    logger.info(
        "Indexing config: embedding_model={} device={} batch_size={}",
        embedding_config.model_name,
        embedding_config.device,
        embedding_config.batch_size or "default",
    )
    logger.info(
        "Indexing config: vectorstore_backend={} persist_dir={} reset_on_startup={}",
        vectorstore_config.backend,
        vectorstore_config.persist_dir,
        vectorstore_config.reset_on_startup,
    )
    logger.info(
        "Indexing config: chunk_size={} chunk_overlap={} pattern={}",
        chunk_size,
        chunk_overlap,
        pattern,
    )
    
    # Initialize embedding model if not provided
    if embedding_model is None:
        logger.info("Loading embedding model...")
        embedding_model = build_configured_embeddings(model_name=embedding_model_name)
        logger.info(
            "Embedding model loaded: model={} device={}",
            embedding_config.model_name,
            embedding_config.device,
        )
    
    if vectorstore is None:
        logger.info(
            "Using configured vector store backend for indexing: {}",
            vectorstore_config.backend,
        )
    
    # Initialize RAG with chunking parameters
    logger.info("Initializing RAG system with chunker...")
    rag = FactDataRAG(
        embeddings=embedding_model,
        vectorstore=vectorstore,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    logger.info("RAG system initialized")
    
    # Chunk and index markdown files
    logger.info(f"Chunking and indexing markdown files from {markdown_dir}...")
    chunk_ids = rag.index_markdown_directory(markdown_dir, pattern=pattern)
    
    logger.info("=" * 70)
    logger.success(f"Pipeline complete! Indexed {len(chunk_ids)} chunks")
    logger.info("=" * 70)
    logger.info("RAG system ready for queries. Use rag.search(query, k=5)")
    
    return rag


__all__ = ["run_fact_data_indexing_pipeline"]
