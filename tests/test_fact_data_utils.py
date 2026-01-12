"""
Tests for fact data extraction utilities and chunker helpers.
"""

import pytest

pytest.importorskip("langchain_text_splitters")

from pathlib import Path

from adsp.data_pipeline.fact_data_pipeline.extract_raw.utils import (
    encode_image_base64,
    strip_json_markdown,
)
from adsp.data_pipeline.fact_data_pipeline.rag.chunker import FactDataMarkdownChunker, estimate_tokens


def test_strip_json_markdown_plain_text():
    assert strip_json_markdown("{\"a\": 1}") == "{\"a\": 1}"


def test_strip_json_markdown_with_fence():
    payload = """
```json
{"a": 1}
```
"""
    assert strip_json_markdown(payload) == "{\"a\": 1}"


def test_strip_json_markdown_multiple_blocks():
    payload = """
```text
ignore
```
```json
{"b": 2}
```
"""
    assert strip_json_markdown(payload) == "{\"b\": 2}"


def test_strip_json_markdown_fallback_to_largest():
    payload = """
```text
short
```
```text
longer block
```
"""
    assert strip_json_markdown(payload) == "longer block"


def test_encode_image_base64_reads_bytes(tmp_path: Path):
    path = tmp_path / "image.png"
    path.write_bytes(b"fake image data")
    encoded, mime = encode_image_base64(path)
    assert mime == "image/png"
    assert isinstance(encoded, str)
    assert encoded


def test_remove_markdown_links():
    text = "See [link](http://example.com) for details."
    assert FactDataMarkdownChunker._remove_markdown_links(text) == "See link for details."


def test_extract_header_lines():
    content = "# Segment: A\n## Page: 1\n### Section: Intro\nBody"
    header = FactDataMarkdownChunker._extract_header_lines(content)
    assert "Segment: A" in header
    assert "Page: 1" in header
    assert "Section: Intro" in header


def test_estimate_tokens_simple():
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("abcdefgh") == 2


def test_chunk_markdown_text_basic():
    chunker = FactDataMarkdownChunker(chunk_size=200, chunk_overlap=0, min_chunk_size=1)
    content = "# Segment: A\n## Page: 1\n### Section: Intro\n\nBody text."
    chunks = chunker.chunk_markdown_text(content, source_file="page_1.md", page_number=1)
    assert len(chunks) >= 1
    assert "Body text" in chunks[0].page_content
