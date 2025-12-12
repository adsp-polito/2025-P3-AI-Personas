# Application: REST API Server (FastAPI)

**Code**: `adsp/app/api_server.py`

## Purpose

Expose the Application layer over HTTP so external clients (frontend/UI, tools, other services) can interact with:
- authentication
- persona discovery
- persona chat (Q&A)
- ingestion (upload)
- reports

The server is designed for local development and demos. It wires existing in-process services (`adsp/app/*`) and returns typed JSON responses.

## Key technologies

- **FastAPI**: REST framework + OpenAPI generation
- **Pydantic**: request/response validation (reuses `adsp/core/types.py`)
- **Uvicorn**: ASGI server

Dependencies are declared in `requirements.txt` (`fastapi`, `uvicorn[standard]`).

## Runtime architecture (in-process)

On startup, the API server creates and stores service singletons:

- `AuthService` (`adsp/app/auth_service.py`)
- `QAService` (`adsp/app/qa_service.py`) → uses Core orchestrator with local RAG + persona loading
- `IngestionService` (`adsp/app/ingestion_service.py`) → writes to `object_store` shim
- `ReportService` (`adsp/app/report_service.py`) → writes markdown to `reports/api/` by default

These are accessible to endpoints via a FastAPI dependency (`get_services()`).

## Authentication model (dev)

If `ADSP_REQUIRE_AUTH=true`, protected endpoints require:
- `X-User: <user>`
- `X-Token: <token>`

Register tokens via:
- `POST /v1/auth/register`

When `ADSP_REQUIRE_AUTH` is unset/false, endpoints are open for local demo convenience.

## Swagger / OpenAPI

- Swagger UI: `GET /docs`
- OpenAPI JSON: `GET /openapi.json`
- ReDoc: `GET /redoc`

## Endpoints

### System

- `GET /health`
  - Returns `{ "status": "ok", "version": "0.1.0" }`

### Auth

- `POST /v1/auth/register`
  - Body: `{ "user": "...", "token": "..." }`
  - Response: `{ "status": "ok" }`

- `POST /v1/auth/validate`
  - Body: `{ "user": "...", "token": "..." }`
  - Response: `{ "authorized": true|false }`

### Personas

- `GET /v1/personas`
  - Response: `{ "personas": [ { "persona_id": "...", "persona_name": "...", "summary_bio": "..." } ] }`

- `GET /v1/personas/{persona_id}/profile`
  - Response model: `PersonaProfileModel` (`adsp/data_pipeline/schema.py`)

- `GET /v1/personas/{persona_id}/system-prompt`
  - Response: `{ "system_prompt": "..." }`

### Chat

- `POST /v1/chat`
  - Body model: `ChatRequest` (`adsp/core/types.py`)
  - Response: `{ "response": ChatResponse }`
  - `ChatResponse` includes `answer`, plus retrieved `context` and `citations` when available.

### Ingestion

- `POST /v1/ingestion/upload`
  - Body: `{ "filename": "...", "content_base64": "...", "bucket": "optional" }`
  - Response: `{ "bucket": "...", "key": "...", "size_bytes": 123 }`

### Reports

- `POST /v1/reports/{persona_id}`
  - Body: `{ "insights": { ... } }`
  - Response: `{ "path": "reports/api/<persona_id>_report.md" }`

## How to run locally

```bash
make install
python scripts/run_api.py
```

Then open:
- `http://localhost:8000/docs`

## Configuration

Environment variables (see `.env.example`):

- API:
  - `ADSP_API_HOST` (default `0.0.0.0`)
  - `ADSP_API_PORT` (default `8000`)
  - `ADSP_API_RELOAD` (default `true`)
  - `ADSP_REQUIRE_AUTH` (default `false`)
- Data paths:
  - `ADSP_PERSONAS_DIR`
  - `ADSP_PERSONA_TRAITS_DIR`
- Runtime LLM backend (optional):
  - `ADSP_LLM_BACKEND=stub|openai`
  - `ADSP_LLM_BASE_URL`, `ADSP_LLM_MODEL`, `ADSP_LLM_API_KEY`

