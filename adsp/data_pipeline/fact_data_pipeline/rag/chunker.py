"""Markdown chunking for fact data to ensure compatibility with embedding models."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from loguru import logger


class FactDataMarkdownChunker:
    """Chunks markdown files for embedding with all-mpnet-base-v2 model.
    
    The all-mpnet-base-v2 model has a maximum sequence length of 384 tokens.
    We use a conservative chunk size to ensure no truncation occurs.
    """
    
    # all-mpnet-base-v2 has max 384 tokens
    # Using ~300 chars per token as rough estimate, and leaving buffer
    DEFAULT_CHUNK_SIZE = 1200  # characters (~300-350 tokens)
    DEFAULT_CHUNK_OVERLAP = 50  # characters for context continuity
    
    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        min_chunk_size: int = 50,
    ):
        """
        Initialize the chunker.
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Overlap between chunks for context
            min_chunk_size: Minimum chunk size to avoid tiny fragments
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
        # Define markdown headers to split on (preserves structure)
        self.headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        
        # Initialize splitters
        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            strip_headers=False,
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
    
    def chunk_markdown_file(
        self,
        file_path: Path,
        page_number: Optional[int] = None,
    ) -> List[Document]:
        """
        Chunk a single markdown file.
        
        Args:
            file_path: Path to the markdown file
            page_number: Optional page number to include in metadata
            
        Returns:
            List of Document objects with chunked content
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Extract page number from filename if not provided
            if page_number is None:
                # Assuming filename format: page_0001.md
                try:
                    page_number = int(file_path.stem.split("_")[-1])
                except (ValueError, IndexError):
                    page_number = 0
            
            return self.chunk_markdown_text(content, file_path.name, page_number)
            
        except Exception as e:
            logger.error(f"Failed to chunk {file_path.name}: {e}")
            return []
    
    @staticmethod
    def _remove_markdown_links(text: str) -> str:
        """Remove markdown links but keep the link text.
        
        Converts [link text](url) to link text
        """
        # Remove markdown links: [text](url) -> text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # Remove reference-style links: [text][ref] -> text
        text = re.sub(r'\[([^\]]+)\]\[[^\]]+\]', r'\1', text)
        return text
    
    @staticmethod
    def _extract_header_lines(content: str) -> str:
        """Extract the first three lines (Segment, Page, Section) from markdown content.
        
        Returns:
            The first three lines as a string, or empty string if not found
        """
        lines = content.split('\n')
        header_lines = []
        
        for line in lines[:10]:  # Check first 10 lines to be safe
            stripped = line.strip()
            if stripped.startswith('# Segment:') or \
               stripped.startswith('## Page:') or \
               stripped.startswith('### Section:'):
                header_lines.append(stripped)
            if len(header_lines) == 3:
                break
        
        return '\n'.join(header_lines) if header_lines else ''

    def chunk_markdown_text(
        self,
        content: str,
        source_file: str = "",
        page_number: int = 0,
    ) -> List[Document]:
        """
        Chunk markdown text content.
        
        Args:
            content: Markdown text content
            source_file: Source filename for metadata
            page_number: Page number for metadata
            
        Returns:
            List of Document objects with chunked content
        """
        # Extract header lines
        header_prefix = self._extract_header_lines(content)
        
        # Remove markdown links but keep link text
        content = self._remove_markdown_links(content)
        
        if not content.strip():
            return []
        
        # First split by markdown headers to preserve structure
        header_splits = self.markdown_splitter.split_text(content)
        
        # Then further split large sections
        chunks: List[Document] = []
        for idx, doc in enumerate(header_splits):
            # Check if document needs further splitting
            if len(doc.page_content) <= self.chunk_size:
                # Small enough, prepend header and keep as is
                content_with_header = f"{header_prefix}\n\n{doc.page_content}" if header_prefix else doc.page_content
                chunks.append(
                    self._add_metadata(
                        Document(page_content=content_with_header, metadata=doc.metadata),
                        source_file, page_number, idx
                    )
                )
            else:
                # Split into smaller chunks
                sub_chunks = self.text_splitter.split_documents([doc])
                for sub_idx, sub_doc in enumerate(sub_chunks):
                    chunk_id = f"{idx}_{sub_idx}"
                    # Prepend header to each sub-chunk
                    content_with_header = f"{header_prefix}\n\n{sub_doc.page_content}" if header_prefix else sub_doc.page_content
                    chunks.append(
                        self._add_metadata(
                            Document(page_content=content_with_header, metadata=sub_doc.metadata),
                            source_file, page_number, chunk_id
                        )
                    )
        
        # Filter out very small chunks
        chunks = [c for c in chunks if len(c.page_content.strip()) >= self.min_chunk_size]
        
        logger.debug(
            f"Chunked {source_file}: {len(content)} chars -> {len(chunks)} chunks"
        )
        
        return chunks
    
    def _add_metadata(
        self,
        doc: Document,
        source_file: str,
        page_number: int,
        chunk_id: any,
    ) -> Document:
        """Add metadata to a document chunk."""
        metadata = doc.metadata.copy() if doc.metadata else {}
        
        # Add chunk-specific metadata
        metadata.update({
            "source_file": source_file,
            "page_number": page_number,
            "chunk_id": str(chunk_id),
        })
        return Document(page_content=doc.page_content, metadata=metadata)
    
    def chunk_directory(
        self,
        directory: Path,
        pattern: str = "page_*.md",
    ) -> List[Document]:
        """
        Chunk all markdown files in a directory.
        
        Args:
            directory: Directory containing markdown files
            pattern: Glob pattern for matching files
            
        Returns:
            List of all Document chunks from all files
        """
        directory = Path(directory)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        all_chunks: List[Document] = []
        markdown_files = sorted(directory.glob(pattern))
        
        logger.info(f"Chunking {len(markdown_files)} markdown files from {directory}")
        
        for file_path in markdown_files:
            chunks = self.chunk_markdown_file(file_path)
            all_chunks.extend(chunks)
        
        logger.info(
            f"Chunked {len(markdown_files)} files into {len(all_chunks)} total chunks"
        )
        
        return all_chunks


def estimate_tokens(text: str) -> int:
    """
    Rough estimate of token count for all-mpnet-base-v2.
    
    Uses a simple heuristic: ~4 characters per token on average.
    """
    return len(text) // 4


__all__ = ["FactDataMarkdownChunker", "estimate_tokens"]
