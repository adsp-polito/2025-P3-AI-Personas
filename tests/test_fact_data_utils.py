"""Fact data extraction utilities and chunker helpers."""

from pathlib import Path

import pytest

pytest.importorskip('langchain_text_splitters')

from adsp.data_pipeline.fact_data_pipeline.extract_raw.utils import (
    encode_image_base64,
    fast_file_hash,
    strip_json_markdown,
)
from adsp.data_pipeline.fact_data_pipeline.rag.chunker import (
    FactDataMarkdownChunker,
    estimate_tokens,
)


def write_markdown(path: Path, content: str) -> None:
    path.write_text(content, encoding='utf-8')


def test_strip_json_markdown_plain_text():
    raw = '{"a": 1}'
    assert strip_json_markdown(raw) == raw


def test_strip_json_markdown_with_fence():
    payload = """
```json
{"a": 1}
```
"""
    assert strip_json_markdown(payload) == '{"a": 1}'


def test_strip_json_markdown_multiple_blocks():
    payload = """
```text
ignore
```
```json
{"b": 2}
```
"""
    assert strip_json_markdown(payload) == '{"b": 2}'


def test_strip_json_markdown_fallback_to_largest():
    payload = """
```text
short
```
```text
longer block
```
"""
    assert strip_json_markdown(payload) == 'longer block'


def test_strip_json_markdown_trims_whitespace():
    payload = '  {\n  "a": 1\n}  '
    assert strip_json_markdown(payload) == '{\n  "a": 1\n}'


def test_strip_json_markdown_array():
    payload = """
```json
[1, 2, 3]
```
"""
    assert strip_json_markdown(payload) == '[1, 2, 3]'


def test_encode_image_base64_reads_bytes(tmp_path: Path):
    path = tmp_path / 'image.png'
    path.write_bytes(b'fake image data')

    encoded, mime = encode_image_base64(path)

    assert mime == 'image/png'
    assert isinstance(encoded, str)
    assert encoded


def test_encode_image_base64_with_max_bytes_no_compress(tmp_path: Path):
    path = tmp_path / 'image.png'
    payload = b'tiny image data'
    path.write_bytes(payload)

    encoded, mime = encode_image_base64(path, max_bytes=1024)

    assert mime == 'image/png'
    assert isinstance(encoded, str)
    assert encoded


def test_fast_file_hash_same_content_same_hash(tmp_path: Path):
    path = tmp_path / 'a.pdf'
    path.write_bytes(b'%PDF-1.4\\nexample-data')

    first = fast_file_hash(path)
    second = fast_file_hash(path)

    assert first == second
    assert isinstance(first, str)
    assert first


def test_fast_file_hash_changes_when_file_changes(tmp_path: Path):
    path = tmp_path / 'a.pdf'
    path.write_bytes(b'%PDF-1.4\\nexample-data-v1')
    first = fast_file_hash(path)

    path.write_bytes(b'%PDF-1.4\\nexample-data-v2')
    second = fast_file_hash(path)

    assert first != second


def test_remove_markdown_links_inline():
    text = 'See [link](http://example.com) for details.'
    assert FactDataMarkdownChunker._remove_markdown_links(text) == 'See link for details.'


def test_remove_markdown_links_reference():
    text = 'See [link][ref] for details.'
    assert FactDataMarkdownChunker._remove_markdown_links(text) == 'See link for details.'


def test_extract_header_lines():
    content = '# Segment: A\n## Page: 1\n### Section: Intro\nBody'
    header = FactDataMarkdownChunker._extract_header_lines(content)

    assert 'Segment: A' in header
    assert 'Page: 1' in header
    assert 'Section: Intro' in header


def test_estimate_tokens_simple():
    assert estimate_tokens('abcd') == 1
    assert estimate_tokens('abcdefgh') == 2


def test_estimate_tokens_respects_boundaries():
    assert estimate_tokens('') == 0
    assert estimate_tokens('12345678') == 2


def test_chunk_markdown_text_basic():
    chunker = FactDataMarkdownChunker(chunk_size=200, chunk_overlap=0, min_chunk_size=1)
    content = '# Segment: A\n## Page: 1\n### Section: Intro\n\nBody text.'

    chunks = chunker.chunk_markdown_text(content, source_file='page_1.md', page_number=1)

    assert len(chunks) >= 1
    assert 'Body text' in chunks[0].page_content
    assert chunks[0].metadata.get('page_number') == 1
    assert chunks[0].metadata.get('source_file') == 'page_1.md'


def test_chunk_markdown_text_empty_content_returns_empty():
    chunker = FactDataMarkdownChunker(chunk_size=200, chunk_overlap=0, min_chunk_size=1)
    chunks = chunker.chunk_markdown_text('', source_file='page_2.md', page_number=2)

    assert chunks == []


def test_chunk_markdown_file_reads_from_disk(tmp_path: Path):
    chunker = FactDataMarkdownChunker(chunk_size=200, chunk_overlap=0, min_chunk_size=1)
    path = tmp_path / 'page_0001.md'
    write_markdown(path, '# Segment: A\n## Page: 1\n### Section: Intro\n\nBody.')

    chunks = chunker.chunk_markdown_file(path)

    assert len(chunks) >= 1
    assert chunks[0].metadata.get('source_file') == 'page_0001.md'
    assert chunks[0].metadata.get('page_number') == 1


def test_chunk_markdown_file_reads_hash_prefixed_name(tmp_path: Path):
    chunker = FactDataMarkdownChunker(chunk_size=200, chunk_overlap=0, min_chunk_size=1)
    path = tmp_path / 'abc123_page_12.md'
    write_markdown(path, '# Segment: A\\n## Page: 12\\n### Section: Intro\\n\\nBody.')

    chunks = chunker.chunk_markdown_file(path)

    assert len(chunks) >= 1
    assert chunks[0].metadata.get('source_file') == 'abc123_page_12.md'
    assert chunks[0].metadata.get('page_number') == 12


def test_chunk_markdown_file_missing_returns_empty(tmp_path: Path):
    chunker = FactDataMarkdownChunker(chunk_size=200, chunk_overlap=0, min_chunk_size=1)
    missing = tmp_path / 'missing.md'
    chunks = chunker.chunk_markdown_file(missing)
    assert chunks == []


def test_chunk_directory_recursively_includes_subdirectories(tmp_path: Path):
    chunker = FactDataMarkdownChunker(chunk_size=200, chunk_overlap=0, min_chunk_size=1)
    nested = tmp_path / 'nested'
    nested.mkdir()

    write_markdown(tmp_path / 'page_1.md', '# Segment: A\n## Page: 1\n### Section: Intro\n\nRoot.')
    write_markdown(nested / 'page_2.md', '# Segment: A\n## Page: 2\n### Section: Intro\n\nNested.')

    chunks = chunker.chunk_directory(tmp_path, pattern='*.md')

    source_files = {chunk.metadata.get('source_file') for chunk in chunks}
    assert 'page_1.md' in source_files
    assert 'page_2.md' in source_files
