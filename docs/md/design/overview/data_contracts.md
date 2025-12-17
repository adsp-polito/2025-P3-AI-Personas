# Data Contracts & Schemas

This system’s behavior depends on a few core payloads that move between layers (persona profile JSON, prompts, extraction outputs, retrieval context).

## Persona profile (canonical)

**Source of truth**
- Extraction pipeline outputs: `data/processed/personas/personas.json` and `data/processed/personas/individual/*.json`
- Pydantic model: `adsp/data_pipeline/schema.py` (`PersonaProfileModel`)
- Human-readable doc: `docs/md/persona_profile_schema.md`

**Key fields (high level)**
- Identity: `persona_id`, `persona_name`
- Description: `visual_description`, `summary_bio`
- Evidence: `indicators[]` (each indicator contains `statements[]`, `metrics[]`, and `sources[]`)
- Traceability: `source_pages[]`, `document`
- Optional reasoning enrichment:
  - `key_indicators[]` (salient statements, derived)
  - `style_profile`, `value_frame`, `reasoning_policies`, `content_filters`

## Orchestrator request/response

**Current in-process call**
- Input: `persona_id: str`, `query: str`
- Output: `response: str`

In production the same contract typically becomes an HTTP/gRPC endpoint:
- Request: `{ persona_id, query, attachments?, session_id? }`
- Response: `{ answer, citations?, explanation?, tool_calls?, latency_ms? }`

See: `docs/md/design/core/orchestrator.md`

## Page-level extraction output (intermediate)

Produced by `PersonaExtractionPipeline` and stored under `data/interim/persona_extraction/`:

- **Rendered pages**: `page_images/page_XXXX.png`
- **Raw page responses**: `pages/page_XXXX.json`
  - `{ page, parsed, error, raw_text }`
- **Structured pages dump** (optional): `pages_structured.json`

Core typed representation:
- `adsp/data_pipeline/persona_data_pipeline/extract_raw/models.py`
  - `PageImage { page_number, image_path, width, height }`
  - `PageExtractionResult { page_number, raw_text, parsed, error }`

## Retrieval context (RAG)

Two retriever paths exist today:

1. **Core stub retriever** (used by `Orchestrator`):
   - `adsp/storage/vector_db.py` returns a string context via `VectorDatabase.search()`

2. **LangChain-based indicator retriever** (data-pipeline utility):
   - `adsp/data_pipeline/persona_data_pipeline/rag/indicator.py`
   - `PersonaIndicatorRAG.search()` returns `langchain_core.documents.Document[]`
   - `documents_to_context_prompt()` converts documents into a prompt-ready context string

See: `docs/md/design/data_pipeline/indicator_rag.md` and `docs/md/design/core/rag_pipeline.md`

