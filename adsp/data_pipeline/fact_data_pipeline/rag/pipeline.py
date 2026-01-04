"""Pipeline function to chunk and index fact data markdown files."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from loguru import logger

from .indicator import FactDataRAG


def run_fact_data_indexing_pipeline(
    markdown_dir: Path,
    embedding_model: Optional[Embeddings] = None,
    embedding_model_name: str = "sentence-transformers/all-mpnet-base-v2",
    chunk_size: int = 1200,
    chunk_overlap: int = 50,
    pattern: str = "page_*.md",
    vectorstore: Optional[InMemoryVectorStore] = None,
) -> FactDataRAG:
    """
    Run the complete fact data indexing pipeline: chunk markdown files and index into RAG.
    
    Args:
        markdown_dir: Directory containing markdown files to index
        embedding_model: Optional pre-initialized embedding model. If None, will create from embedding_model_name
        embedding_model_name: HuggingFace model name for embeddings (default: all-mpnet-base-v2)
        chunk_size: Maximum chunk size in characters (default: 1200)
        chunk_overlap: Overlap between chunks in characters (default: 50)
        pattern: Glob pattern for markdown files (default: page_*.md)
        vectorstore: Optional pre-initialized vector store. If None, creates InMemoryVectorStore
        
    Returns:
        FactDataRAG instance with indexed data ready for search
    """
    markdown_dir = Path(markdown_dir)
    
    if not markdown_dir.exists():
        raise FileNotFoundError(f"Markdown directory not found: {markdown_dir}")
    
    logger.info("=" * 70)
    logger.info("Starting Fact Data Indexing Pipeline")
    logger.info("=" * 70)
    logger.info(f"Markdown directory: {markdown_dir}")
    logger.info(f"Embedding model: {embedding_model_name}")
    logger.info(f"Chunk size: {chunk_size} characters")
    logger.info(f"Chunk overlap: {chunk_overlap} characters")
    logger.info(f"File pattern: {pattern}")
    
    # Initialize embedding model if not provided
    if embedding_model is None:
        logger.info("Loading embedding model...")
        embedding_model = HuggingFaceEmbeddings(model_name=embedding_model_name)
        logger.info("Embedding model loaded")
    
    # Initialize vector store if not provided
    if vectorstore is None:
        logger.info("Creating in-memory vector store...")
        vectorstore = InMemoryVectorStore(embedding=embedding_model)
        logger.info("Vector store created")
    
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
